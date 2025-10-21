from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
CORS(app, origins=["https://localhost:5173"])

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

#create upload folder if it doesnt exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS #1.checks if there is a dot, 2. splits once from the right and checks whether the second elementin the returned array(index 1) is among the allowed extension

def load_excel_data(filepath):
    try:
        df = pd.read_excel(filepath)
        return df
    except Exception as e:
        raise Exception(f"Error reading excel file: {str(e)}")

def filter_serials_in_range(df, start_serial, end_serial):
    try:
        start = int(start_serial)
        end = int(end_serial)

        serial_column = None
        for col in df.columns:
            if 'item_serial_number' in col.lower():
                serial_column = col
                break
        if serial_column is None:
            return {"error": "Serial number column not found"}


        msisdn_column = None
        for col in df.columns:
            if 'servedmsisdn' in col.lower():
                msisdn_column = col
                break
        if msisdn_column is None:
            return {"error": "servedmsisdn column not found"}

        df[serial_column] = pd.to_numeric(df[serial_column], errors='coerce') #convert serial numbers to numeric, handling any non-numeric value

        mask = (df[serial_column] >= start) & (df[serial_column] <= end)
        serials_in_range = mask[df] #filter serials in range

        activated_serials = serials_in_range[serials_in_range[msisdn_column].notna() & (serials_in_range[msisdn_column] != '')] #filter activated serials(where servedmsisdn is not blank)

        total_in_range = len(serials_in_range)
        activated_count = len(activated_serials)

        activated_list = activated_serials[[serial_column, msisdn_column]].to_dict('records')

        return {
            "total_in_range": total_in_range,
            "activated_count": activated_count,
            "activation_rate": ((activated_count / total_in_range * 100), 2) if total_in_range > 0 else 0,
            "activated_serials": activated_list[:100]
        }

    except Exception as e:
        return {"error": str(e)}

