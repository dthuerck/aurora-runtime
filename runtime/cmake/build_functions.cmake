# returns: object files (VE_OBJECTS) to link into the final executable
function(ve_build_offload) # source files: ARGV / ARGN

    # define path for output folders (for the runtime script)
    set(__KERNEL_WORK_DIR "${CMAKE_CURRENT_BINARY_DIR}/ve_kernels")
    set(__WRAPPER_WORK_DIR "${CMAKE_CURRENT_BINARY_DIR}/ve_wrappers")
    set(__OFFLOAD_WORK_DIR "${CMAKE_CURRENT_BINARY_DIR}/ve_offload")

    # create output folders (llvm, ncc) in current binary dir
    file(MAKE_DIRECTORY ${__KERNEL_WORK_DIR})
    file(MAKE_DIRECTORY ${__WRAPPER_WORK_DIR})
    file(MAKE_DIRECTORY ${__OFFLOAD_WORK_DIR})

    # collect paths for the vecc driver (includes for headers, )
    set(__VECC_INCLUDE_DIRS "")
    foreach(path ${AURORA_INCLUDE_DIRS})
        set(__VECC_INCLUDE_DIRS "${__VECC_INCLUDE_DIRS} --includedir ${path}")
    endforeach()

    # included headers
    set(__VECC_INCLUDE_DIRS "${__VECC_INCLUDE_DIRS} --includedir ${CMAKE_SOURCE_DIR}/../../header")

    # determine paths of runtime-generated source code files and create a
    # VECC call to generate them
    set(__KERNEL_NAMES "")
    set(__KERNEL_HEADERS "")
    set(__KERNEL_SOURCES "")
    set(__WRAPPER_HEADERS "")
    set(__WRAPPER_SOURCES "")
    set(__OFFLOAD_HEADERS "")
    set(__OFFLOAD_SOURCES "")
    foreach(f ${ARGV})
        get_filename_component(__f_base ${f} NAME_WE)
        set(__f "${CMAKE_SOURCE_DIR}/${f}")

        set(__f_kernel_header "${__KERNEL_WORK_DIR}/${__f_base}_kernels.h")
        set(__f_kernel_source "${__KERNEL_WORK_DIR}/${__f_base}_kernels.c")
        set(__f_wrapper_header "${__WRAPPER_WORK_DIR}/${__f_base}_wrappers.h")
        set(__f_wrapper_source "${__WRAPPER_WORK_DIR}/${__f_base}_wrappers.c")
        set(__f_offload_header "${__OFFLOAD_WORK_DIR}/${__f_base}_offload.h")
        set(__f_offload_source "${__OFFLOAD_WORK_DIR}/${__f_base}_offload.c")

        add_custom_command(
            VERBATIM
            OUTPUT ${__f_kernel_header} ${__f_kernel_source} ${} ${__f_wrapper_header} ${__f_wrapper_source} ${__f_offload_header} ${__f_offload_source}
            COMMAND /bin/bash -c "python ${AURORA_VECC_SCRIPT} ${__VECC_INCLUDE_DIRS} --kerneldir ${__KERNEL_WORK_DIR} --wrapperdir ${__WRAPPER_WORK_DIR} --offloaddir ${__OFFLOAD_WORK_DIR} ${__f}"
            DEPENDS ${f})

        list(APPEND __KERNEL_HEADERS ${__f_kernel_header})
        list(APPEND __KERNEL_SOURCES ${__f_kernel_source})
        list(APPEND __WRAPPER_HEADERS ${__f_wrapper_header})
        list(APPEND __WRAPPER_SOURCES ${__f_wrapper_source})
        list(APPEND __OFFLOAD_HEADERS ${__f_offload_header})
        list(APPEND __OFFLOAD_SOURCES ${__f_offload_source})
    endforeach()

    # create a common symbol table for all generated kernel files
    add_custom_command(
        VERBATIM
        OUTPUT "ve_kernel_names.h"
        COMMAND /bin/bash -c "python ${AURORA_SYMBOL_TABLE_SCRIPT} --wrapperdir ${__WRAPPER_WORK_DIR} ${CMAKE_BINARY_DIR}"
        DEPENDS ${ARGV}
    )

    # compile kernel code using LLVM
    set(__KERNEL_OBJECTS "")
    foreach(src ${__KERNEL_SOURCES})

        # define output file
        get_filename_component(__src_dir ${src} DIRECTORY)
        get_filename_component(__src_name ${src} NAME)
        set(__o_file "${__src_dir}/${__src_name}.o")

        add_custom_command(
            VERBATIM
            OUTPUT ${__o_file}
            COMMAND ${AURORA_CLANG_EXECUTABLE} ${AURORA_LCFLAGS} -c ${src} -o ${__o_file}
            DEPENDS ${src})

        list(APPEND __KERNEL_OBJECTS ${__o_file})
    endforeach()

    # compile (OMP) wrapper code using NCC
    set(__WRAPPER_OBJECTS "")
    foreach(src ${__WRAPPER_SOURCES})

        # define output file
        get_filename_component(__src_dir ${src} DIRECTORY)
        get_filename_component(__src_name ${src} NAME)
        set(__o_file "${__src_dir}/${__src_name}.o")

        add_custom_command(
            VERBATIM
            OUTPUT ${__o_file}
            COMMAND ${AURORA_NCC_EXECUTABLE} ${AURORA_NCFLAGS} -c ${src} -o ${__o_file}
            DEPENDS ${src})

        list(APPEND __WRAPPER_OBJECTS ${__o_file})
    endforeach()

    # add device kernels for init
    SET(__initkern_src ${CMAKE_SOURCE_DIR}/../../runtime/include/aurora_runtime_kernels.c)
    SET(__initkern_obj ${CMAKE_BINARY_DIR}/aurora_runtime_kernels.o)
    add_custom_command(
        VERBATIM
        OUTPUT ${__initkern_obj}
        COMMAND ${AURORA_NCC_EXECUTABLE} ${AURORA_NCFLAGS} -c ${__initkern_src} -o ${__initkern_obj}
        DEPENDS ${__initkern_src})
        list(APPEND __WRAPPER_OBJECTS ${__initkern_obj})

    # link devide-side objects into a single object file (ve_kernels.o)
    string(REPLACE ";" " " __KERNEL_OBJECTS_STR "${__KERNEL_OBJECTS}")
    string(REPLACE ";" " " __WRAPPER_OBJECTS_STR "${__WRAPPER_OBJECTS}")
    foreach(path ${AURORA_LIBRARY_DIRS})
        list(APPEND __LIBDIR_STR -L${path})
    endforeach()
    foreach(lib ${AURORA_LIBRARIES})
        list(APPEND __LIB_STR -l${lib})
    endforeach()

    set(__VEORUN_PATH "${CMAKE_CURRENT_BINARY_DIR}/ve_kernels.o")
    add_custom_command(
        OUTPUT ${__VEORUN_PATH}
        COMMAND ${CMAKE_COMMAND} -E env CFLAGS="${AURORA_NCFLAGS}" LDFLAGS="${__LIBDIR_STR} ${__LIB_STR}" ${AURORA_MKVEORUNSTATIC_EXECUTABLE} ${__VEORUN_PATH} ${__WRAPPER_OBJECTS} ${__KERNEL_OBJECTS} ${AURORA_OBJECTS}
        COMMAND chmod +x ${__VEORUN_PATH}
        DEPENDS ${__KERNEL_OBJECTS} ${__WRAPPER_OBJECTS})

    # build offload code + runtime) using the host compiler
    foreach(path ${AURORA_INCLUDE_DIRS})
        list(APPEND __CC_INCLUDES -I${path})
    endforeach()

    set(__VE_OBJECTS "")
    foreach(src ${__OFFLOAD_SOURCES})

        # define output file
        get_filename_component(__src_dir ${src} DIRECTORY)
        get_filename_component(__src_name ${src} NAME)
        set(__o_file "${__src_dir}/${__src_name}.o")

        add_custom_command(
            VERBATIM
            OUTPUT ${__o_file}
            COMMAND ${CMAKE_C_COMPILER} -w ${AURORA_CFLAGS} -D__VEO_STRUCTS__ -I${__AURORA_VEOFFLOAD_INCLUDE_DIR} -I${__AURORA_UDMA_INCLUDE_DIR} -I${__AURORA_RUNTIME_INCLUDE_DIR} -c ${src} -o ${__o_file}
            DEPENDS ${src})

        list(APPEND __VE_OBJECTS ${__o_file})
    endforeach()

    SET(__runtime_src ${CMAKE_SOURCE_DIR}/../../runtime/include/aurora_runtime.c)
    SET(__runtime_obj ${CMAKE_BINARY_DIR}/aurora_runtime.o)
    add_custom_command(
        VERBATIM
        OUTPUT ${__runtime_obj}
        COMMAND ${CMAKE_C_COMPILER} -w ${AURORA_CFLAGS} -D__VEO_STRUCTS__ -I${__AURORA_VEOFFLOAD_INCLUDE_DIR} -I${__AURORA_UDMA_INCLUDE_DIR} -I${__AURORA_RUNTIME_INCLUDE_DIR} -I${CMAKE_BINARY_DIR} -c ${__runtime_src}  -o ${__runtime_obj}
        DEPENDS ${__runtime_src} "ve_kernel_names.h")
    list(APPEND __VE_OBJECTS ${__runtime_obj})

    # return VE_OBJECTS to parent scope
    set(VE_OBJECTS "${__VE_OBJECTS}" PARENT_SCOPE)

    add_custom_target(
        build-ve-objects
        DEPENDS ${__VE_OBJECTS} ${__VEORUN_PATH})

endfunction()

function(ve_add_executable TARGET)

    set(__source_files ${ARGV})
    list(REMOVE_AT __source_files 0)

    add_executable(${TARGET}
        ${__source_files})
    target_compile_options(${TARGET}
        PRIVATE -fopenmp)
    # target_link_options(${TARGET}
    #     PRIVATE -fopenmp)
    set_target_properties(${TARGET}
        PROPERTIES LINK_FLAGS "-fopenmp")
    add_dependencies(${TARGET}
        build-ve-objects)
    target_link_libraries(${TARGET}
        ${VE_OBJECTS}
        pthread
        ${AURORA_HOST_LIBRARIES})

endfunction()