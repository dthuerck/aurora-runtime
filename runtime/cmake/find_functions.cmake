function(find_file_rec_cached VAR FILE BASE_PATHS)

    if("${${VAR}}" STREQUAL "")
        message("-- Locating path of file ${FILE}...")

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
            set(${VAR} ${__item} CACHE INTERNAL "${VAR}")
            # set(${VAR} ${__item} PARENT_SCOPE)
            message("-- Found: ${__item}")
        else()
            if("${__tmp}" STREQUAL "")
            message(FATAL_ERROR "${FILE} not found.")
            endif()
        endif()
    endif()

endfunction()

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
        message("-- Found: ${__item}")
    else()
        if("${__tmp}" STREQUAL "")
        message(FATAL_ERROR "${FILE} not found.")
        endif()
    endif()

endfunction()

function(find_path_rec_cached VAR FILE BASE_PATH)

    if("${${VAR}}" STREQUAL "")
        find_file_rec(__tmp ${FILE} "${BASE_PATH}")
        get_filename_component(__path ${__tmp} DIRECTORY)
        set(${VAR} ${__path} CACHE INTERNAL "${VAR}")
    endif()
    
endfunction()