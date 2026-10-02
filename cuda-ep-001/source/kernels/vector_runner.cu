// AUTO-GENERATED runner embedding the VERBATIM frozen elementwise_add_kernel.
// Reads n, a[n], b[n] (float32 LE) from argv[1]; writes out[n] to argv[2].
#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>

__global__ void elementwise_add_kernel(const float* a, const float* b, float* out, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        out[idx] = a[idx] + b[idx];
    }
}

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: runner in.bin out.bin\n"); return 2; }
    FILE* fi = fopen(argv[1], "rb");
    if (!fi) { fprintf(stderr, "cannot open input\n"); return 2; }
    int n = 0;
    if (fread(&n, sizeof(int), 1, fi) != 1) { fprintf(stderr, "bad n\n"); return 2; }
    float* h_a = (float*)malloc(n * sizeof(float));
    float* h_b = (float*)malloc(n * sizeof(float));
    float* h_out = (float*)malloc(n * sizeof(float));
    if (fread(h_a, sizeof(float), n, fi) != (size_t)n) { return 2; }
    if (fread(h_b, sizeof(float), n, fi) != (size_t)n) { return 2; }
    fclose(fi);

    float *d_a, *d_b, *d_out;
    size_t bytes = n * sizeof(float);
    cudaMalloc(&d_a, bytes); cudaMalloc(&d_b, bytes); cudaMalloc(&d_out, bytes);
    cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice);
    int threads = 256; int blocks = (n + threads - 1) / threads;
    elementwise_add_kernel<<<blocks, threads>>>(d_a, d_b, d_out, n);
    cudaError_t err = cudaDeviceSynchronize();
    if (err != cudaSuccess) { fprintf(stderr, "cuda err: %s\n", cudaGetErrorString(err)); return 3; }
    cudaMemcpy(h_out, d_out, bytes, cudaMemcpyDeviceToHost);
    cudaFree(d_a); cudaFree(d_b); cudaFree(d_out);

    FILE* fo = fopen(argv[2], "wb");
    fwrite(h_out, sizeof(float), n, fo);
    fclose(fo);
    free(h_a); free(h_b); free(h_out);
    return 0;
}
