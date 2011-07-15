//#version 130

in vec3 aPosition;
in vec4 aColor; // This is the per-vertex color


// matrices
uniform mat4 projMatrix;
uniform mat4 modelviewMatrix;
uniform int textureWidth;

out vec4 vColor0;   // This is the output to the geometry shader
out float vWidth;

uniform sampler2D widthSampler;

void main()
{

        // fetch texture value
        vec4 widthVec;
        // retrieve texture position

        int x = gl_VertexID % textureWidth;
        int y = gl_VertexID / textureWidth;

        //widthVec = texelFetch(widthSampler, gl_VertexID, 0); // needs version 130
        widthVec = texelFetch(widthSampler, ivec2(x,y), 0); // needs version 130

        float width;
        width = widthVec.x; // We have to fetch a vec4 from the texture, but we will
                            // use a format like GL_LUMINANCE32 which fetches to (L,L,L,1)
                            // so we can just read one component
        vWidth = width;

        vColor0 = vec4(aColor.x , aColor.y , aColor.z, aColor.w); // Pass from VS -> GS

        // Personally, I use uniform buffers containing the modelview and the projection matrix, as well as the MVP
        // matrix in order to avoid unnecessary matrix multiplication on a per-vertex basis.

        // gl_Position = gl_ModelViewProjectionMatrix * vec4(aPosition.x , aPosition.y, aPosition.z, 1.0);

        gl_Position = projMatrix * modelviewMatrix * vec4(aPosition.x , aPosition.y, aPosition.z, 1.0);

}
