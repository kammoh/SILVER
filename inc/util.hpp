/*
 * -----------------------------------------------------------------
 * COMPANY : Ruhr-Universit�t Bochum, Chair for Security Engineering
 * AUTHOR  : Pascal Sasdrich (pascal.sasdrich@rub.de)
 * DOCUMENT: https://doi.org/10.1007/978-3-030-64837-4_26
 *           https://eprint.iacr.org/2020/634.pdf
 * -----------------------------------------------------------------
 *
 * Copyright (c) 2020, Pascal Sasdrich
 *
 * All rights reserved.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTERS BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Please see LICENSE and README for license and further instructions.
 */

#ifndef __UTIL_HPP_
#define __UTIL_HPP_

#include "config.hpp"

#include <set>
#include <map>
#include <cmath>
#include <chrono>
#include <vector>
#include <string>
#include <sstream>
#include <fstream>
#include <iostream>
#include <algorithm>
#include <functional>

#ifndef DOUBLE_COMPARE_THRESHOLD
#define DOUBLE_COMPARE_THRESHOLD 0.000001
#endif

/**
 * @brief Definition of supported unary and binary operations.
 */
std::set<std::string> unary   = {"out", "reg", "not"};
std::set<std::string> binary  = {"and", "nand", "or", "nor", "xor", "xnor"};

/**
 * @brief Definition of possible probe positions for standard and robust probing.
 */
std::set<std::string> rprobes = {"reg", "out"};
std::set<std::string> sprobes = {"in", "ref", "not", "and", "nand", "or", "nor", "xor", "xnor"};

std::string strip(const std::string &s)
{
    // Remove leading whitespaces
    auto start = s.find_first_not_of(" \t\n\r");

    // Return empty string if input is empty
    if (start == std::string::npos) {
        return "";
    }

    // Remove trailing whitespaces
    auto end = s.find_last_not_of(" \t\n\r");

    // Return stripped string
    return s.substr(start, end - start + 1);
}

std::string strip_comments(const std::string &line)
{
    // Remove comments
    auto pos = line.find_first_of("#");
    if (pos != std::string::npos) {
        return line.substr(0, pos);
    }

    return line;
}

std::vector<std::string>
split(const std::string line, char delimiter)
{
    // Variable declarations
    std::vector<std::string> tokens;
    std::string token;

    // Turn string into stream
    std::stringstream stream(line);

    // Extract tokens from line
    while(getline(stream, token, delimiter)) {
        token = strip(token);
        if (token.empty() || ((token.length() == 1) && (token[0] == delimiter))) {
            continue;
        }
        tokens.push_back(token);
    }

    return tokens;
}

#endif // ___UTIL_HPP_
