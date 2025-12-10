#pragma once

#include <string>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <stdint.h>

typedef struct {
    uint32_t ne;
    uint32_t nx;
    uint32_t ny;
    uint32_t nz;
    double e_min;
    double e_max;
    double x_min;
    double x_max;
    double y_min;
    double y_max;
    double z_min;
    double z_max;
} MeshInfo;

int parse_header(const std::vector<std::string>& header_lines, MeshInfo &mesh_info);
int read_dat(std::string filename, std::vector<std::string>& header_lines, MeshInfo &mesh_info, std::vector<double>& values);