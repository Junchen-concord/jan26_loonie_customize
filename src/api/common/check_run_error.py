def check_run_error(output_final_dict, version="v1"):
    if "runError" in output_final_dict:
        if version == "v2":
            error_details = output_final_dict["summaryInfo"][0]["runMsg"]
            error_code = output_final_dict["summaryInfo"][0]["runError"]
            output_json_v2 = {
                "accounts": [],
                "customerInfo": {},
                "transactions": [],
                "errorDetails": error_details,
                "runError": error_code,
                "modelVersion": output_final_dict["modelVersion"],
            }
            return output_json_v2
        return output_final_dict
    return None
