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

# Utility rule file for build_smtc_sensor_webrtc.

# Include the progress variables for this target.
include sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/progress.make

sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/webrtc && ../../../sensor/webrtc/build.sh Xeon stadium 1 1,0,0,0,1 1,0,0,0,1 gst INT8,FP32 

build_smtc_sensor_webrtc: sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc
build_smtc_sensor_webrtc: sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/build.make

.PHONY : build_smtc_sensor_webrtc

# Rule to build all files generated by this target.
sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/build: build_smtc_sensor_webrtc

.PHONY : sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/build

sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/clean:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/webrtc && $(CMAKE_COMMAND) -P CMakeFiles/build_smtc_sensor_webrtc.dir/cmake_clean.cmake
.PHONY : sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/clean

sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/depend:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/sensor/webrtc /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/webrtc /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : sensor/webrtc/CMakeFiles/build_smtc_sensor_webrtc.dir/depend

