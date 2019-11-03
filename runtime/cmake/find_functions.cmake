function(find_file_rec VAR FILE BASE_PATHS)

# generate glob expressions
set(__globs "")
foreach(p ${BASE_PATHS})
    list(APPEND __globs "${p}/**/${FILE}")
    list(APPEND __globs "${p}/${FILE}")
endforeach(p)    
file(
    GLOB_RECURSE
    __lst
    ${__globs})
if(NOT __lst STREQUAL "")
    list(GET __lst 0 __item)
    set(${VAR} ${__item} PARENT_SCOPE)
endif()

endfunction()

function(find_path_rec VAR FILE BASE_PATH)
    find_file_rec(__tmp ${FILE} "${BASE_PATH}")
    get_filename_component(__path ${__tmp} DIRECTORY)
    set(${VAR} ${__path} PARENT_SCOPE)
endfunction()