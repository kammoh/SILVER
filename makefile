
BOOST    ?= /opt/homebrew/opt/boost
SYLVAN_CFLAGS := $(shell pkg-config sylvan --cflags)
SYLVAN_LIBS := $(shell pkg-config sylvan --libs)
GMP_LIBS := $(shell pkg-config gmp --libs)
BOOST_LIBS := -L$(BOOST)/lib -lboost_program_options
BOOST_CFLAGS := -I$(BOOST)/include

TARGET	 := verify

SRC_EXT	 := cpp
INC_EXT  := hpp

BLD_DIR	 := ./build
SRC_DIR	 := ./src
BIN_DIR	 := ./bin
INC_DIR  := ./inc
LIB_DIR	 := ./lib
OBJ_DIR	 := $(BLD_DIR)/objects

CXXFLAGS := $(SYLVAN_CFLAGS) $(BOOST_CFLAGS) -I$(INC_DIR) -DVERILOG -std=c++11
LDFLAGS := $(SYLVAN_LIBS) $(GMP_LIBS) $(BOOST_LIBS)


SOURCES  := $(wildcard $(SRC_DIR)/*.cpp)
HEADERS  := $(wildcard $(SRC_DIR)/*.hpp) $(wildcard $(INC_DIR)/**/*.hpp) $(wildcard $(INC_DIR)/**/*.h)
# SOURCES  := $(shell find $(SRC_DIR) -name '*.$(SRC_EXT)' | sort -k 1nr | cut -f2-)
OBJECTS  := $(SOURCES:$(SRC_DIR)/%.$(SRC_EXT)=$(OBJ_DIR)/%.o)

all: build $(BIN_DIR)/$(TARGET)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp $(HEADERS)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $(INCLUDE) -o $@ -c $<

$(BIN_DIR)/$(TARGET): $(OBJECTS)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $(INCLUDE) $(LDFLAGS) -o $(BIN_DIR)/$(TARGET) $(OBJECTS) $(LIBRARIES)

.PHONY: all build clean debug release

build:
	@mkdir -p $(BIN_DIR)
	@mkdir -p $(OBJ_DIR)

debug: CXXFLAGS += -DDEBUG -g -O0
debug: all

release: CXXFLAGS += -O3 -mtune=native -fomit-frame-pointer
release: all

clean:
	-@rm -rvf $(OBJ_DIR)/*
	-@rm -rvf $(BIN_DIR)/*
