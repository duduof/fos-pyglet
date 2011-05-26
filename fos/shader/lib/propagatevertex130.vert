#version 130
in vec3 aPosition;
in vec4 aColor; // This is the per-vertex color

// matrices
in mat4 projMatrix;
in mat4 modelviewMatrix;

out vec4 vColor;   // This is the output to the geometry shader
out float vWidth;

uniform sampler1D widthSampler;

void main()
{

        // fetch texture value
        vec4 widthVec;
        widthVec = texelFetch(widthSampler, gl_VertexID, 0); // needs version 130
        float width;
        width = widthVec.x; // We have to fetch a vec4 from the texture, but we will
                            // use a format like GL_LUMINANCE32 which fetches to (L,L,L,1)
                            // so we can just read one component
        vWidth = width;

        vColor = vec4(aColor.x , aColor.y , aColor.z, aColor.w); // Pass from VS -> GS

        // Personally, I use uniform buffers containing the modelview and the projection matrix, as well as the MVP
        // matrix in order to avoid unnecessary matrix multiplication on a per-vertex basis.

        //gl_Position = gl_ModelViewProjectionMatrix * vec4(aPosition.x , aPosition.y, aPosition.z, 1.0);

        gl_Position = modelviewMatrix * projMatrix * vec4(aPosition.x , aPosition.y, aPosition.z, 1.0);;

}
