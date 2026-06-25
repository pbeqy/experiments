//! Process switch record support.

use super::{TaskContext, TaskControlBlock};
use crate::sync::UPSafeCell;
use lazy_static::*;

const MAX_SWITCH_RECORDS: usize = 128;

#[derive(Copy, Clone)]
struct ProcessSnapshot {
    exists: bool,
    pid: usize,
    tcb_addr: usize,
    task_context_addr: usize,
    task_status: &'static str,
    ra: usize,
    sp: usize,
    s: [usize; 12],
}

impl ProcessSnapshot {
    const fn boot_state() -> Self {
        Self {
            exists: false,
            pid: 0,
            tcb_addr: 0,
            task_context_addr: 0,
            task_status: "Boot",
            ra: 0,
            sp: 0,
            s: [0; 12],
        }
    }

    fn from_task(pid: usize, task: &TaskControlBlock) -> Self {
        Self {
            exists: true,
            pid,
            tcb_addr: task as *const TaskControlBlock as usize,
            task_context_addr: &task.task_cx as *const TaskContext as usize,
            task_status: task.task_status.as_str(),
            ra: task.task_cx.ra(),
            sp: task.task_cx.sp(),
            s: task.task_cx.s(),
        }
    }
}

#[derive(Copy, Clone)]
struct SwitchRecord {
    sequence: usize,
    old_process: ProcessSnapshot,
    new_process: ProcessSnapshot,
}

impl SwitchRecord {
    const fn empty() -> Self {
        Self {
            sequence: 0,
            old_process: ProcessSnapshot::boot_state(),
            new_process: ProcessSnapshot::boot_state(),
        }
    }
}

struct SwitchRecorder {
    records: [SwitchRecord; MAX_SWITCH_RECORDS],
    count: usize,
}

impl SwitchRecorder {
    const fn new() -> Self {
        Self {
            records: [SwitchRecord::empty(); MAX_SWITCH_RECORDS],
            count: 0,
        }
    }
}

lazy_static! {
    static ref SWITCH_RECORDER: UPSafeCell<SwitchRecorder> =
        unsafe { UPSafeCell::new(SwitchRecorder::new()) };
}

/// Record the first switch from boot state to the first task.
pub(super) fn record_first_switch(next_pid: usize, next_task: &TaskControlBlock) {
    let record = SwitchRecord {
        sequence: 0,
        old_process: ProcessSnapshot::boot_state(),
        new_process: ProcessSnapshot::from_task(next_pid, next_task),
    };
    save_and_print(record);
}

/// Record a normal switch from the old running task to the new task.
pub(super) fn record_task_switch(
    old_pid: usize,
    old_task: &TaskControlBlock,
    new_pid: usize,
    new_task: &TaskControlBlock,
) {
    let record = SwitchRecord {
        sequence: 0,
        old_process: ProcessSnapshot::from_task(old_pid, old_task),
        new_process: ProcessSnapshot::from_task(new_pid, new_task),
    };
    save_and_print(record);
}

fn save_and_print(mut record: SwitchRecord) {
    let mut recorder = SWITCH_RECORDER.exclusive_access();
    record.sequence = recorder.count + 1;
    if recorder.count < MAX_SWITCH_RECORDS {
        let index = recorder.count;
        recorder.records[index] = record;
        recorder.count += 1;
    }
    drop(recorder);
    print_switch_record(&record);
}

fn print_switch_record(record: &SwitchRecord) {
    println!();
    println!("|----------------------------------------------------------------------------------------|");
    println!("|                                    Switch #{}                                          |", record.sequence);
    println!("|----------------------------------------------------------------------------------------|");
    print_old_process(&record.old_process);
    print_new_process(&record.new_process);
}

fn print_old_process(process: &ProcessSnapshot) {
    if !process.exists {
        println!("[OLD PROCESS] - No Previous Process (Boot State)");
        return;
    }
    println!("[OLD PROCESS] - Process Being Interrupted/Switched Out");
    print_process_snapshot(process);
}

fn print_new_process(process: &ProcessSnapshot) {
    println!("[NEW PROCESS] - Process Being Switched In");
    print_process_snapshot(process);
}

fn print_process_snapshot(process: &ProcessSnapshot) {
    println!("Process ID (PID): {}", process.pid);
    println!("TCB Address: {:#x}", process.tcb_addr);
    println!("Task Context Address: {:#x}", process.task_context_addr);
    println!("PID: {}", process.pid);
    println!("Task Status: {}", process.task_status);
    println!("Kernel Stack Top: {:#x}", process.sp);
    println!("User Stack Top: {:#x}", 0);
    println!("Entry Point: {:#x}", process.ra);
    println!("ra (Return Address): {:#x}", process.ra);
    println!("sp (Stack Pointer): {:#x}", process.sp);
    println!("s0 (Frame Pointer): {:#x}", process.s[0]);
    println!("s1: {:#x}", process.s[1]);
    println!("s2: {:#x}", process.s[2]);
    println!("s3: {:#x}", process.s[3]);
    println!("s4: {:#x}", process.s[4]);
    println!("s5: {:#x}", process.s[5]);
    println!("s6: {:#x}", process.s[6]);
    println!("s7: {:#x}", process.s[7]);
    println!("s8: {:#x}", process.s[8]);
    println!("s9: {:#x}", process.s[9]);
    println!("s10: {:#x}", process.s[10]);
    println!("s11: {:#x}", process.s[11]);
}
