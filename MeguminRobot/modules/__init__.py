from MeguminRobot import LOAD, LOGGER, NO_LOAD


def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    # Ini menghasilkan daftar modul di folder ini agar * di __main__ berfungsi.
    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    if LOAD or NO_LOAD:
        to_load = LOAD
        if to_load:
            if not all(
                any(mod == module_name for module_name in all_modules)
                for mod in to_load
            ):
                LOGGER.error("Nama urutan pemuatan tidak valid.  Berhenti.")
                quit(1)

            all_modules = sorted(set(all_modules) - set(to_load))
            to_load = list(all_modules) + to_load

        else:
            to_load = all_modules

        if NO_LOAD:
            LOGGER.info("Tidak memuat: {}".format(NO_LOAD))
            return [item for item in to_load if item not in NO_LOAD]

        return to_load

    return all_modules


ALL_MODULES = __list_all_modules()
LOGGER.info("Modul untuk dimuat: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]




