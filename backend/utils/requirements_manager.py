import json
import re
import sys
import subprocess
import threading


def get_installed_requirements(python_path):
    res = subprocess.run(
        [python_path, "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True
    )
    return res

def collect_installed_requirements(python_path, _canon_name) -> dict:
        """
        Collects packages from the SAME environment used for installs
        (self._python_path -m pip list --format=json). Falls back to
        importlib.metadata if pip listing fails.
        Returns: {canonical_name: {'name': str, 'version': str}}
        """
        installed: dict[str, dict[str, str]] = {}

        res =  get_installed_requirements(python_path)
        

        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            for pkg in data:
                name = pkg.get("name") or ""
                ver = pkg.get("version") or ""
                if name:
                    canon = _canon_name(name)
                    installed[canon] = {"name": name, "version": ver}
            if installed:
                return installed

        return installed




def reinstall_packages(python_path, requirements, ok, errors):
    for pkg_name, spec in requirements:
        print(pkg_name, spec)
        try:
            # Uninstall first (only for mismatches)
            res_un = subprocess.run(
                [python_path, "-m", "pip", "uninstall", "-y", pkg_name],
                capture_output=True, text=True,
            )
            print(res_un)
            if res_un.returncode not in (0, 1):
                print('errored')
                errors.append(f"Uninstall {pkg_name} returned {res_un.returncode}:\n{res_un.stderr.strip() or res_un.stdout.strip()}")

            # Install desired version (allow bare if spec is '')
            target = f"{pkg_name}{spec}"
            print(target, pkg_name)
            res_in = subprocess.run(
                [python_path, "-m", "pip", "install", "--upgrade", target],
                capture_output=True, text=True,
            )
            print(res_in)
            if res_in.returncode != 0:
                ok = False
                errors.append(f"Install {target} failed:\n{res_in.stderr.strip() or res_in.stdout.strip()}")

        except Exception as e:
            ok = False
            errors.append(f"{pkg_name}{spec}: {e}")
    
    return ok, errors

def install_packages(python_path, requirements, ok, errors):
    for pkg_name, spec in requirements:
        try:
            target = f"{pkg_name}{spec}"
            res = subprocess.run(
                [python_path, "-m", "pip", "install", "--upgrade", target],
                capture_output=True, text=True,
            )
            if res.returncode != 0:
                ok = False
                errors.append(f"Install {target} failed:\n{res.stderr.strip() or res.stdout.strip()}")
        except Exception as e:
            ok = False
            errors.append(f"{pkg_name}{spec}: {e}")
        
    return ok, errors

def install_requirements_txt(python_path, path):
    result = subprocess.run(
        [python_path, "-m", "pip", "install", "-r", path],
        capture_output=True,
        text=True
    )
    return result

def freeze_requirements(python_path):
    result = subprocess.run(
        [python_path, "-m", "pip", "freeze"],
        capture_output=True,
        text=True
    )
    return result

def uninstall_requirements(python_path, chunk):
    proc = subprocess.run(
        [python_path, "-m", "pip", "uninstall", "-y", *chunk],
        capture_output=True,
        text=True
    )
    return proc

def install_single_requirement(python_path, requirement_name):
    result = subprocess.run(
        [python_path, "-m", "pip", "install", "--upgrade", requirement_name],
        capture_output=True,
        text=True
    )
    return result

def uninstall_single_requirement(python_path, requirement_name):
    result = subprocess.run(
        [python_path,  "-m", "pip", "uninstall", "-y", requirement_name],
        capture_output=True,
        text=True
    )
    return result
