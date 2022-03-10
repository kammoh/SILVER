
CXX 	 := g++
CXXFLAGS := -DVERILOG -std=c++11


TARGET	 := silver
SYLVAN_DIR ?= /usr/local
SYLVAN_INCLUDE_DIR ?= $(SYLVAN_DIR)/include
SYLVAN_LIB_DIR ?= $(SYLVAN_DIR)/lib

BOOST_DIR ?= /usr
BOOST_INCLUDE_DIR ?= $(BOOST_DIR)/include
BOOST_LIB_DIR ?= $(BOOST_DIR)/lib

SRC_EXT	 := cpp
INC_EXT  := hpp

BLD_DIR	 := ./build
SRC_DIR	 := ./src
BIN_DIR	 := ./bin
OBJ_DIR	 := $(BLD_DIR)/objects

LDFLAGS  := -L$(SYLVAN_LIB_DIR) -lsylvan -L$(BOOST_LIB_DIR) -lboost_program_options

# SOURCES  := $(wildcard $(SRC_DIR)/*.cpp)
SOURCES  := $(shell find $(SRC_PATH) -name '*.$(SRC_EXT)' | sort -k 1nr | cut -f2-)
OBJECTS  := $(SOURCES:$(SRC_DIR)/%.$(SRC_EXT)=$(OBJ_DIR)/%.o)
INCLUDE	 := -I$(SYLVAN_INCLUDE_DIR) -I$(BOOST_INCLUDE_DIR) -I./inc

all: build $(BIN_DIR)/$(TARGET)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $(INCLUDE) -o $@ -c $<

$(BIN_DIR)/$(TARGET): $(OBJECTS)
	@mkdir -p $(@D)
	$(CXX) -o $(BIN_DIR)/$(TARGET) $(OBJECTS) $(LDFLAGS) 

.PHONY: all build clean debug release

build:
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(OBJ_DIR)

debug: CXXFLAGS += -DDEBUG -g
debug: all

release: CXXFLAGS += -march=native -mtune=native -O3 -fomit-frame-pointer
release: all

clean:
	-@rm -rvf $(OBJ_DIR)/*
	-@rm -rvf $(BIN_DIR)/*
