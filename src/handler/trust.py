import bpy
from bpy.app.handlers import persistent
from ..lib import trust as trust_lib


@persistent
def tmy_save_recalc_handler(scene):
    if trust_lib.is_file_trusted(only_explicit_trust=True):
        try:
            trust_lib.save_trust_hash()
            print("Added a Tell Me Why trust hash for this version of the file")
        except trust_lib.AlreadyTrustedException:
            print("Formulas did not change. Did not add a Tell Me Why trust hash.")
        except trust_lib.NoFormulasException:
            print("Formulas were all removed. Did not add a Tell Me Why trust hash.")
        except trust_lib.AllTrustDisabledException:
            print("Tell Me Why Formula evaluation has been entirely disabled. Aborting trust evaluation.")
            return
    else:
        print("Formulas were not trusted. Not creating a TMY trust hash.")


@persistent
def tmy_load_trust_handler(scene):
    try:
        trusted = trust_lib.trust_if_known()
        print(f"This file's Tell Me Why formulas {'are' if trusted else 'are not yet'} trusted")
    except trust_lib.NoFormulasException:
        trust_lib.trust_if_no_formulas()
        print("This file contains no Tell Me Why formulas. Trusting formulas for the session.")
    except trust_lib.AllTrustDisabledException:
        print("Tell Me Why Formula evaluation has been entirely disabled. Aborting trust evaluation.")
        return


REGISTER_HANDLERS = {
    "load_post": (tmy_load_trust_handler,),
    "save_pre": (tmy_save_recalc_handler,),
}

