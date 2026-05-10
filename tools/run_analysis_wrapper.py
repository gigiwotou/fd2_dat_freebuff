import sys
import subprocess

result = subprocess.run(
    [sys.executable, "D:\\workspace\\fd2_dat_freebuff\\tools\\analyze_fdother_final.py"],
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
