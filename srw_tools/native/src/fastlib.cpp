#include "fastlib.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <sstream>
#include <cctype>

extern "C" {

double fast_sum(const double* data, size_t length) {
    double sum = 0.0;
    for (size_t i = 0; i < length; ++i) {
        sum += data[i];
    }
    return sum;
}

// (no helper read_dat_header function implemented currently)

int fast_load_file(const char* path, char*** headers, size_t* n_headers, double** values, size_t* n_values) {
    if (!path || !headers || !n_headers || !values || !n_values) return -1;
    FILE* f = std::fopen(path, "r");
    if (!f) return -2;
    std::vector<std::string> header_lines;
    std::vector<double> vals;
    bool in_header = true;
    // Use portable line reading
    char buffer[4096];
    while (fgets(buffer, sizeof(buffer), f)) {
        std::string s(buffer);
        while (!s.empty() && (s.back() == '\n' || s.back() == '\r')) s.pop_back();
        if (in_header && !s.empty() && s[0] == '#') {
            size_t pos = 1;
            while (pos < s.size() && isspace(static_cast<unsigned char>(s[pos]))) pos++;
            header_lines.push_back(s.substr(pos));
            continue;
        }
        in_header = false;
        std::istringstream iss(s);
        std::string tok;
        while (iss >> tok) {
            try {
                double v = std::stod(tok);
                vals.push_back(v);
            } catch (...) {
                // skip tokens that don't parse as double
            }
        }
    }
    fclose(f);

    size_t hcount = header_lines.size();
    char** harr = nullptr;
    if (hcount > 0) {
        harr = (char**)malloc(hcount * sizeof(char*));
        for (size_t i = 0; i < hcount; ++i) {
            const std::string &s = header_lines[i];
            char* copy = (char*)malloc(s.size() + 1);
            std::memcpy(copy, s.c_str(), s.size() + 1);
            harr[i] = copy;
        }
    }

    size_t vcount = vals.size();
    double* varr = nullptr;
    if (vcount > 0) {
        varr = (double*)malloc(vcount * sizeof(double));
        for (size_t i = 0; i < vcount; ++i) {
            varr[i] = vals[i];
        }
    }

    *headers = harr;
    *n_headers = hcount;
    *values = varr;
    *n_values = vcount;
    return 0;
}

void fast_free_string_array(char** arr, size_t n) {
    if (!arr) return;
    for (size_t i = 0; i < n; ++i) {
        free(arr[i]);
    }
    free(arr);
}

void fast_free_double_array(double* arr) {
    if (!arr) return;
    free(arr);
}

void fast_scale(double* data, size_t length, double scale) {
    for (size_t i = 0; i < length; ++i) {
        data[i] *= scale;
    }
}

}
