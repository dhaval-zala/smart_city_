# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.10

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:


#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:


# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list


# Suppress display of executed commands.
$(VERBOSE).SILENT:


# A target that is always out of date.
cmake_force:

.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build

# Utility rule file for build_smtc_sensor_simulation.

# Include the progress variables for this target.
include sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/progress.make

sensor/simulation/CMakeFiles/build_smtc_sensor_simulation:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/simulation && ../../../sensor/simulation/build.sh Xeon stadium 1 1,0,0,0,1 1,0,0,0,1 gst INT8,FP32 

build_smtc_sensor_simulation: sensor/simulation/CMakeFiles/build_smtc_sensor_simulation
build_smtc_sensor_simulation: sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/build.make

.PHONY : build_smtc_sensor_simulation

# Rule to build all files generated by this target.
sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/build: build_smtc_sensor_simulation

.PHONY : sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/build

sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/clean:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/simulation && $(CMAKE_COMMAND) -P CMakeFiles/build_smtc_sensor_simulation.dir/cmake_clean.cmake
.PHONY : sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/clean

sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/depend:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/sensor/simulation /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/simulation /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : sensor/simulation/CMakeFiles/build_smtc_sensor_simulation.dir/depend
