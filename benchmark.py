import multiprocessing
import time
import math
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def single_core_prime_worker(start, end):
    count = 0
    total = end - start

    with Progress(
        TextColumn("🔄 [bold]{task.fields[mode]}[/bold]"),
        BarColumn(bar_width=30, complete_style="green", finished_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>5.1f}%"),
        TextColumn("ETA:"),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("Calculating", total=total, mode="Single-Core")

        for i, num in enumerate(range(start, end), 1):
            if is_prime(num):
                count += 1
            if i % 1000 == 0 or i == total:
                progress.update(task, advance=1000 if i % 1000 == 0 else total % 1000)

    return {'primes': count}

def multi_worker(start, end, result_dict, idx, progress_dict):
    count = 0
    total = end - start
    for i, num in enumerate(range(start, end), 1):
        if is_prime(num):
            count += 1
        if i % 1000 == 0 or i == total:
            progress_dict[idx] = i
    result_dict[idx] = count

def benchmark_primes(start_range=1, end_range=1_000_000, difficulty=1.0):
    adjusted_end = int(end_range * difficulty)
    print(f"\n🎯 Benchmarking Prime Numbers")
    print(f"🎮 Difficulty: {difficulty:.1f}x")
    print(f"🔁 Range     : {start_range:,} to {adjusted_end:,}\n")

    # 🔹 SINGLE-CORE
    t0 = time.time()
    single_result = single_core_prime_worker(start_range, adjusted_end)
    t1 = time.time()
    single_time = t1 - t0
    single_score = int(single_result['primes'] / single_time)

    print("\n📊 Single-Core Benchmark:")
    print(f"{'Primes Found':<25}: {single_result['primes']:,}")
    print(f"{'Elapsed Time':<25}: {single_time:.2f} s")
    print(f"{'Score':<25}: {single_score:,} (Primes/sec)")

    # 🔸 MULTI-CORE
    cpu_count = multiprocessing.cpu_count()
    chunk_size = (adjusted_end - start_range) // cpu_count

    manager = multiprocessing.Manager()
    result_dict = manager.dict()
    progress_dict = manager.dict()

    print(f"\n⚙️  Multi-Core Benchmark: Using {cpu_count} cores...")

    with Progress(
        TextColumn("🔄 [bold]{task.fields[mode]}[/bold]"),
        BarColumn(bar_width=30, complete_style="green", finished_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>5.1f}%"),
        TextColumn("ETA:"),
        TimeRemainingColumn(),
    ) as progress:

        task = progress.add_task("Computing", total=adjusted_end - start_range, mode="Multi-Core")
        processes = []

        for i in range(cpu_count):
            chunk_start = start_range + i * chunk_size
            chunk_end = adjusted_end if i == cpu_count - 1 else chunk_start + chunk_size
            p = multiprocessing.Process(target=multi_worker, args=(chunk_start, chunk_end, result_dict, i, progress_dict))
            processes.append(p)
            p.start()

        while any(p.is_alive() for p in processes):
            done = sum(progress_dict.get(i, 0) for i in range(cpu_count))
            progress.update(task, completed=done)
            time.sleep(0.2)
        progress.update(task, completed=adjusted_end - start_range)

        for p in processes:
            p.join()

    total_primes = sum(result_dict.values())
    multi_time = progress.tasks[0].finished_time
    avg_time = multi_time / cpu_count if cpu_count else multi_time
    multi_score = int(total_primes / avg_time)

    print("\n📊 Multi-Core Benchmark:")
    print(f"{'Primes Found':<25}: {total_primes:,}")
    print(f"{'Total Time':<25}: {multi_time:.2f} s")
    print(f"{'Avg Time per Core':<25}: {avg_time:.2f} s")
    print(f"{'Score':<25}: {multi_score:,} (Primes/sec)")

    boost = round(multi_score / single_score, 2) if single_score else 0
    print("\n📈 Comparison Summary:")
    print(f"{'🧠 Single-Core Score':<25}: {single_score:,}")
    print(f"{'🧠 Multi-Core Score':<25}: {multi_score:,}")
    print(f"{'🚀 Multi-Core Boost':<25}: {boost}x faster")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            difficulty = float(sys.argv[1])
        except ValueError:
            print("❌ Invalid difficulty value. Please enter a numeric value.")
            sys.exit(1)
    else:
        try:
            user_input = input("Enter difficulty level (default = 3.0): ").strip()
            difficulty = float(user_input) if user_input else 3.0
        except ValueError:
            print("❌ Invalid input. Falling back to default difficulty = 3.0")
            difficulty = 3.0

    benchmark_primes(difficulty=difficulty)
