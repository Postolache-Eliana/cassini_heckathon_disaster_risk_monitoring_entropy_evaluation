import os
import sys
try:
    import moderngl
    import numpy as np
    from PIL import Image
except ImportError:
    print("Dependencies missing! Please install them via:")
    print("pip install moderngl numpy Pillow")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python gpu_fast_corners.py <path_to_image.jpg>")
        return

    img_path = sys.argv[1]
    
    print("--- GPU Accelerated FAST Corner Detection Proof-of-Concept ---")
    
    # Initialize a headless ModernGL context. 
    # On Pi Zero, this connects to the VideoCore IV EGL driver.
    try:
        ctx = moderngl.create_context(standalone=True, require=200)
        print(f"Context initialized: {ctx.info}")
    except Exception as e:
        print(f"Failed to create EGL context. Is the VideoCore driver loaded? Error: {e}")
        return

    # Load image and convert to grayscale
    img = Image.open(img_path).convert('L')
    width, height = img.size
    print(f"Loaded image: {width}x{height}")

    # Load the custom FAST fragment shader
    shader_path = os.path.join(os.path.dirname(__file__), 'fast_shader.glsl')
    with open(shader_path, 'r') as f:
        fragment_shader_code = f.read()

    # Standard vertex shader (just passes through a full-screen quad)
    vertex_shader_code = '''
        precision mediump float;
        attribute vec2 in_position;
        varying vec2 v_texcoord;
        void main() {
            // Map [-1, 1] position to [0, 1] texture coordinates
            v_texcoord = in_position * 0.5 + 0.5;
            // OpenGL texture origin is bottom-left, so we flip Y
            v_texcoord.y = 1.0 - v_texcoord.y; 
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
    '''

    prog = ctx.program(
        vertex_shader=vertex_shader_code,
        fragment_shader=fragment_shader_code
    )

    # Provide uniforms to the shader
    prog['u_tex_size'].value = (1.0 / width, 1.0 / height)
    prog['u_threshold'].value = 0.15  # Adjust FAST threshold here (0.0 to 1.0)

    # Upload image data as a texture to the GPU
    texture = ctx.texture((width, height), 1, img.tobytes())
    texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
    texture.use(location=0)
    prog['u_texture'].value = 0

    # Create a framebuffer to capture the shader output
    fbo_texture = ctx.texture((width, height), 1)
    fbo = ctx.framebuffer(color_attachments=[fbo_texture])
    fbo.use()

    # Create a full-screen quad VBO
    vertices = np.array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
         1.0,  1.0,
    ], dtype='f4')
    vbo = ctx.buffer(vertices.tobytes())
    vao = ctx.simple_vertex_array(prog, vbo, 'in_position')

    print("Executing custom shader on VideoCore IV GPU...")
    # Render! This executes the shader in parallel across the image
    vao.render(moderngl.TRIANGLE_STRIP)

    # Read the resulting mask back from the GPU
    output_bytes = fbo.read(components=1)
    
    # Convert back to an image to visualize the corners
    out_img = Image.frombytes('L', (width, height), output_bytes)
    out_path = img_path.replace('.jpg', '_corners.png')
    out_img.save(out_path)
    
    # Calculate how many corners were found
    mask_array = np.frombuffer(output_bytes, dtype=np.uint8)
    corner_count = np.count_nonzero(mask_array > 128)
    
    print(f"[SUCCESS] GPU processing complete!")
    print(f"Extracted {corner_count} FAST corners.")
    print(f"Saved corner mask visualization to: {out_path}")
    print("\nNext step for ORB-SLAM: Extract BRIEF descriptors at these coordinate locations!")

if __name__ == '__main__':
    main()
