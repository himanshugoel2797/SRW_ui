#pragma once

#include <cstddef>

#ifdef __cplusplus
extern "C" {
#endif

double fast_sum(const double* data, size_t length);
void fast_scale(double* data, size_t length, double scale);

// Read a file: leading comment lines starting with '#' are collected into
// a string array (without the leading '#') and stored in *headers with
// length *n_headers. The remaining tokens are parsed as doubles and
// stored in *values with length *n_values. Memory is allocated with
// malloc and must be freed by the caller using the provided free functions.
// Returns 0 on success; non-zero on error.
int fast_load_file(const char* path, char*** headers, size_t* n_headers, double** values, size_t* n_values);

// Free helper functions for data returned by fast_load_file
void fast_free_string_array(char** arr, size_t n);
void fast_free_double_array(double* arr);

#ifdef __cplusplus
}
#endif
