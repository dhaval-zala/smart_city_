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

# Utility rule file for build_docker_swarm.

# Include the progress variables for this target.
include deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/progress.make

deployment/docker-swarm/CMakeFiles/build_docker_swarm:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/deployment/docker-swarm && ../../../deployment/docker-swarm/build.sh Xeon stadium 1 1,0,0,0,1 1,0,0,0,1 gst INT8,FP32 

build_docker_swarm: deployment/docker-swarm/CMakeFiles/build_docker_swarm
build_docker_swarm: deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/build.make

.PHONY : build_docker_swarm

# Rule to build all files generated by this target.
deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/build: build_docker_swarm

.PHONY : deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/build

deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/clean:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/deployment/docker-swarm && $(CMAKE_COMMAND) -P CMakeFiles/build_docker_swarm.dir/cmake_clean.cmake
.PHONY : deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/clean

deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/depend:
	cd /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/deployment/docker-swarm /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/deployment/docker-swarm /home/desktop6/Desktop/dhaval/Dhaval/Smart-city_new/build/deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : deployment/docker-swarm/CMakeFiles/build_docker_swarm.dir/depend

