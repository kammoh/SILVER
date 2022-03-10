
CXX 	 := g++
CXXFLAGS := -DVERILOG -std=c++11


TARGET	 := silver
SILVAN_INCLUDE_DIR ?= /usr/local/include
SILVAN_LIB_DIR ?= /usr/local/lib64

SRC_EXT	 := cpp
INC_EXT  := hpp

BLD_DIR	 := ./build
SRC_DIR	 := ./src
BIN_DIR	 := ./bin
OBJ_DIR	 := $(BLD_DIR)/objects

LDFLAGS  := -L$(SILVAN_LIB_DIR) -lsylvan -lboost_program_options

# SOURCES  := $(wildcard $(SRC_DIR)/*.cpp)
SOURCES  := $(shell find $(SRC_PATH) -name '*.$(SRC_EXT)' | sort -k 1nr | cut -f2-)
OBJECTS  := $(SOURCES:$(SRC_DIR)/%.$(SRC_EXT)=$(OBJ_DIR)/%.o)
INCLUDE	 := -I$(SILVAN_INCLUDE_DIR) -I./inc

all: build $(BIN_DIR)/$(TARGET)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $(INCLUDE) -o $@ -c $<

$(BIN_DIR)/$(TARGET): $(OBJECTS)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $(INCLUDE) $(LDFLAGS) -o $(BIN_DIR)/$(TARGET) $(OBJECTS)

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
