precision mediump float;
varying vec2 v_texcoord;
uniform sampler2D u_texture;
uniform vec2 u_tex_size; // Example: vec2(1.0/width, 1.0/height)
uniform float u_threshold;

void main() {
    // Read the center pixel (assuming grayscale or using the red channel)
    float p = texture2D(u_texture, v_texcoord).r;

    // 16 pixel offsets for a Bresenham circle of radius 3
    vec2 offsets[16];
    offsets[0]  = vec2( 0.0, -3.0);
    offsets[1]  = vec2( 1.0, -3.0);
    offsets[2]  = vec2( 2.0, -2.0);
    offsets[3]  = vec2( 3.0, -1.0);
    offsets[4]  = vec2( 3.0,  0.0);
    offsets[5]  = vec2( 3.0,  1.0);
    offsets[6]  = vec2( 2.0,  2.0);
    offsets[7]  = vec2( 1.0,  3.0);
    offsets[8]  = vec2( 0.0,  3.0);
    offsets[9]  = vec2(-1.0,  3.0);
    offsets[10] = vec2(-2.0,  2.0);
    offsets[11] = vec2(-3.0,  1.0);
    offsets[12] = vec2(-3.0,  0.0);
    offsets[13] = vec2(-3.0, -1.0);
    offsets[14] = vec2(-2.0, -2.0);
    offsets[15] = vec2(-1.0, -3.0);

    // Sample the 16 ring pixels
    float d[16];
    for (int i = 0; i < 16; i++) {
        d[i] = texture2D(u_texture, v_texcoord + offsets[i] * u_tex_size).r;
    }

    // High-speed rejection test (points 0, 8, 4, 12)
    // A corner must have at least 3 of these 4 points all brighter or all darker
    int b_count = 0;
    int d_count = 0;
    if (d[0]  > p + u_threshold) b_count++; else if (d[0]  < p - u_threshold) d_count++;
    if (d[8]  > p + u_threshold) b_count++; else if (d[8]  < p - u_threshold) d_count++;
    if (d[4]  > p + u_threshold) b_count++; else if (d[4]  < p - u_threshold) d_count++;
    if (d[12] > p + u_threshold) b_count++; else if (d[12] < p - u_threshold) d_count++;

    // If we don't even have 3 out of the main 4, it's definitely not a FAST-9 corner
    if (b_count < 3 && d_count < 3) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black = Not a corner
        return;
    }

    // Full FAST-9 test: we need 9 contiguous pixels that meet the criteria.
    int max_bright_streak = 0;
    int max_dark_streak = 0;
    int current_bright = 0;
    int current_dark = 0;

    // We loop 16+9 times to handle the wrap-around
    for (int i = 0; i < 25; i++) {
        int idx = i;
        if (idx >= 16) idx -= 16; // modulo 16
        
        if (d[idx] > p + u_threshold) {
            current_bright++;
            current_dark = 0;
            if (current_bright > max_bright_streak) max_bright_streak = current_bright;
        } else if (d[idx] < p - u_threshold) {
            current_dark++;
            current_bright = 0;
            if (current_dark > max_dark_streak) max_dark_streak = current_dark;
        } else {
            current_bright = 0;
            current_dark = 0;
        }
    }

    // Output white if it's a corner, black if it's not
    if (max_bright_streak >= 9 || max_dark_streak >= 9) {
        gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0); // Corner!
    } else {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
