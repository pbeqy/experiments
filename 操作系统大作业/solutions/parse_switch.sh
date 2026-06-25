#!/usr/bin/env bash
set -euo pipefail

input_file="${1:-a.txt}"
output_file="${2:-进程上下文切换记录表.csv}"

if [[ ! -f "$input_file" ]]; then
    echo "Input file not found: $input_file" >&2
    exit 1
fi

awk -v output="$output_file" '
BEGIN {
    row_count = 0
    add_row("[OLD PROCESS] - Process Being Interrupted/Switched Out")
    add_row("Process ID (PID)")
    add_row("TCB Address")
    add_row("Task Context Address")
    add_row("PID")
    add_row("Task Status")
    add_row("Kernel Stack Top")
    add_row("User Stack Top")
    add_row("Entry Point")
    add_row("ra (Return Address)")
    add_row("sp (Stack Pointer)")
    add_row("s0 (Frame Pointer)")
    add_row("s1")
    add_row("s2")
    add_row("s3")
    add_row("s4")
    add_row("s5")
    add_row("s6")
    add_row("s7")
    add_row("s8")
    add_row("s9")
    add_row("s10")
    add_row("s11")
    add_row("[NEW PROCESS] - Process Being Switched In")
    add_row("Process ID (PID)")
    add_row("TCB Address")
    add_row("Task Context Address")
    add_row("PID")
    add_row("Task Status")
    add_row("Kernel Stack Top")
    add_row("User Stack Top")
    add_row("Entry Point")
    add_row("ra (Return Address)")
    add_row("sp (Stack Pointer)")
    add_row("s0 (Frame Pointer)")
    add_row("s1")
    add_row("s2")
    add_row("s3")
    add_row("s4")
    add_row("s5")
    add_row("s6")
    add_row("s7")
    add_row("s8")
    add_row("s9")
    add_row("s10")
    add_row("s11")
}

function add_row(title) {
    row_count++
    row_title[row_count] = title
}

function trim(value) {
    gsub(/^[[:space:]|]+/, "", value)
    gsub(/[[:space:]|]+$/, "", value)
    return value
}

function csv_escape(value) {
    gsub(/"/, "\"\"", value)
    return "\"" value "\""
}

function value_after_colon(line) {
    sub(/^[^:]*:[[:space:]]*/, "", line)
    return trim(line)
}

function record_value(title, value) {
    for (i = 1; i <= row_count; i++) {
        if (row_title[i] == title && section_start <= i && i <= section_end) {
            table[i, switch_count] = value
            return
        }
    }
}

function normalize_title(line, title) {
    line = trim(line)
    if (line ~ /Process ID \(PID\):/) return "Process ID (PID)"
    if (line ~ /TCB Address:/) return "TCB Address"
    if (line ~ /Task Context Address:/) return "Task Context Address"
    if (line ~ /PID:/) return "PID"
    if (line ~ /Task Status:/) return "Task Status"
    if (line ~ /Kernel Stack Top:/) return "Kernel Stack Top"
    if (line ~ /User Stack Top:/) return "User Stack Top"
    if (line ~ /Entry Point:/) return "Entry Point"
    if (line ~ /ra \(Return Address\):/) return "ra (Return Address)"
    if (line ~ /sp \(Stack Pointer\):/) return "sp (Stack Pointer)"
    if (line ~ /s0 \(Frame Pointer\):/) return "s0 (Frame Pointer)"
    if (line ~ /s1:/) return "s1"
    if (line ~ /s2:/) return "s2"
    if (line ~ /s3:/) return "s3"
    if (line ~ /s4:/) return "s4"
    if (line ~ /s5:/) return "s5"
    if (line ~ /s6:/) return "s6"
    if (line ~ /s7:/) return "s7"
    if (line ~ /s8:/) return "s8"
    if (line ~ /s9:/) return "s9"
    if (line ~ /s10:/) return "s10"
    if (line ~ /s11:/) return "s11"
    return ""
}

/Switch #[0-9]+/ {
    raw_switch_count++
    if (raw_switch_count >= 2) {
        switch_count++
        active = 1
        mode = ""
    } else {
        active = 0
    }
    next
}

active && /\[OLD PROCESS\] - Process Being Interrupted\/Switched Out/ {
    mode = "old"
    section_start = 1
    section_end = 23
    table[1, switch_count] = ""
    next
}

active && /\[NEW PROCESS\] - Process Being Switched In/ {
    mode = "new"
    section_start = 24
    section_end = 46
    table[24, switch_count] = ""
    next
}

active && mode != "" {
    title = normalize_title($0)
    if (title != "") {
        record_value(title, value_after_colon($0))
        if (title == "s11") {
            mode = ""
        }
    }
}

END {
    printf "%s", csv_escape("Row Title") > output
    for (col = 1; col <= switch_count; col++) {
        printf ",%s", csv_escape("Switch #" col) > output
    }
    printf "\n" > output

    for (row = 1; row <= row_count; row++) {
        printf "%s", csv_escape(row_title[row]) > output
        for (col = 1; col <= switch_count; col++) {
            printf ",%s", csv_escape(table[row, col]) > output
        }
        printf "\n" > output
    }
    print "Parsed " switch_count " valid switches."
    print "Output: " output
}
' "$input_file"
