/*
 * elementwise_add.cu
 * CUDA-EP-001 GPU Phase - Candidate Kernel
 * Remnant Fieldworks Inc. | CUDA-EP-001 | v1.0 | 2026-10-01
 * RESEARCH ONLY - NOT PRODUCTION
 *
 * Task: Elementwise addition of two 1D float32 tensors of size N.
 * Selected because: simplest possible CUDA kernel, deterministic,
 * easy to validate against reference (numpy/torch.add), minimal confounds.
 *
 * Reference implementation: Python numpy elementwise_add_reference()
 */
#include <cuda_runtime.h>
#include <stdio.h>

__global__ void elementwise_add_kernel(const float* a, const float* b, float* out, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        out[idx] = a[idx] + b[idx];
    }
}

// Host wrapper: launches the kernel and copies result to host
void elementwise_add(const float* h_a, const float* h_b, float* h_out, int n) {
    float *d_a, *d_b, *d_out;
    size_t bytes = n * sizeof(float);

    cudaMalloc(&d_a, bytes);
    cudaMalloc(&d_b, bytes);
    cudaMalloc(&d_out, bytes);

    cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice);

    int threads = 256;
    int blocks = (n + threads - 1) / threads;
    elementwise_add_kernel<<<blocks, threads>>>(d_a, d_b, d_out, n);

    cudaDeviceSynchronize();
    cudaMemcpy(h_out, d_out, bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_a);
    cudaFree(d_b);
    cudaFree(d_out);
}

int main() {
    const int N = 1024;
    float h_a[N], h_b[N], h_out[N];

    // Deterministic test inputs
    for (int i = 0; i < N; i++) {
        h_a[i] = (float)i;
        h_b[i] = (float)(N - i);
    }

    elementwise_add(h_a, h_b, h_out, N);

    // Verify: every element should be N
    int pass = 1;
    for (int i = 0; i < N; i++) {
        if (h_out[i] != (float)N) {
            printf("FAIL at index %d: expected %f got %f\n", i, (float)N, h_out[i]);
            pass = 0;
        }
    }
    if (pass) printf("ALL_PASS: elementwise_add N=%d\n", N);
    return pass ? 0 : 1;
}
