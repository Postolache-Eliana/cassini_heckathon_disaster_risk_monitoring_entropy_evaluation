import sys
import os
import pytest

def test_gpu_shader_compilation():
    """
    Test that the VideoCore IV GPU can successfully create a headless 
    EGL context and compile the GLSL FAST corner shader without syntax errors.
    """
    try:
        import moderngl
    except ImportError:
        pytest.skip("moderngl not installed")
        
    try:
        # Require OpenGL ES 2.0 (VideoCore IV target)
        ctx = moderngl.create_context(standalone=True, require=200)
    except Exception as e:
        pytest.fail(f"Failed to create EGL context. Is the Pi graphics driver active? Error: {e}")
        
    shader_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fast_shader.glsl')
    
    if not os.path.exists(shader_path):
        pytest.fail(f"Shader file not found at {shader_path}")
        
    with open(shader_path, 'r') as f:
        fragment_shader_code = f.read()
        
    vertex_shader_code = '''
        precision mediump float;
        attribute vec2 in_position;
        varying vec2 v_texcoord;
        void main() {
            v_texcoord = in_position * 0.5 + 0.5;
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
    '''
    
    try:
        prog = ctx.program(
            vertex_shader=vertex_shader_code,
            fragment_shader=fragment_shader_code
        )
        assert prog is not None
    except Exception as e:
        pytest.fail(f"GLSL Shader compilation failed on VideoCore IV GPU: {e}")
