#include "file_parser.h"
#include <string>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <stdint.h>

int parse_header(const std::vector<std::string>& header_lines, MeshInfo &mesh_info) {
    //Line 0 = Units "#Characteristic [Unit] (...)"
    //Line 1 - initial energy "#Value #Initial Photon Energy [eV]"
    //Line 2 - final energy "#Value #Final Photon Energy [eV]"
    //Line 3 - number of energy points "#Value #Number of points vs Photon Energy"
    //Line 4 - initial x "#Value #Initial Horizontal Position [m]"
    //Line 5 - final x "#Value #Final Horizontal Position [m]"
    //Line 6 - number of x points "#Value #Number of points vs Horizontal Position"
    //Line 7 - initial y "#Value #Initial Vertical Position [m]"
    //Line 8 - final y "#Value #Final Vertical Position [m]"
    //Line 9 - number of y points "#Value #Number of points vs Vertical Position"
    
    if (header_lines.size() < 10) return -1;

    try {
        mesh_info.e_min = std::stod(header_lines[1].substr(header_lines[1].find('#') + 1));
        mesh_info.e_max = std::stod(header_lines[2].substr(header_lines[2].find('#') + 1));
        mesh_info.ne = static_cast<uint32_t>(std::stoul(header_lines[3].substr(header_lines[3].find('#') + 1)));
        mesh_info.x_min = std::stod(header_lines[4].substr(header_lines[4].find('#') + 1));
        mesh_info.x_max = std::stod(header_lines[5].substr(header_lines[5].find('#') + 1));
        mesh_info.nx = static_cast<uint32_t>(std::stoul(header_lines[6].substr(header_lines[6].find('#') + 1)));
        mesh_info.y_min = std::stod(header_lines[7].substr(header_lines[7].find('#') + 1));
        mesh_info.y_max = std::stod(header_lines[8].substr(header_lines[8].find('#') + 1));
        mesh_info.ny = static_cast<uint32_t>(std::stoul(header_lines[9].substr(header_lines[9].find('#') + 1)));
    } catch (...) {
        return -2;
    }
    
    return 0;
}

int read_dat(std::string filename, std::vector<std::string>& header_lines, MeshInfo &mesh_info, std::vector<double>& values) {
    FILE* fd = std::fopen(filename.c_str(), "r");
    if (!fd) return -1;
    char buffer[4096];
    // Read header lines (first 10 lines starting with '#')
    for (int i = 0; i < 10; ++i) {
        if (!fgets(buffer, sizeof(buffer), fd)) break;
        std::string line(buffer);
        if (line.empty() || line[0] != '#') {
            // Not a header line, rewind
            std::fseek(fd, -static_cast<long>(line.size()), SEEK_CUR);
            break;
        }
        // Remove trailing newline
        while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) line.pop_back();
        header_lines.push_back(line.substr(1)); // skip '#'
    }
    if (parse_header(header_lines, mesh_info) != 0) {
        std::fclose(fd);
        return -2;
    }

    // Read data values
    double val;
    while (fscanf(fd, "%lf\n", &val) == 1) {
        values.push_back(val);
    }
    std::fclose(fd);
    return 0;
}