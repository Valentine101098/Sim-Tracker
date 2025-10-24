from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)
# CORS(app, origins=["https://localhost:5173"])
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

#create upload folder if it doesnt exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS #1.checks if there is a dot, 2. splits once from the right and checks whether the second elementin the returned array(index 1) is among the allowed extension

def load_excel_data(filepath): #this fn takes a filepath and attempts to load the excel data into a pandas dataframe
    try:
        df = pd.read_excel(filepath)
        return df
    except Exception as e:
        raise Exception(f"Error reading excel file: {str(e)}")


def parse_date(date_value): #fn converts date-like inputs into a pandas timestamp object
    if pd.isna(date_value): #checks if value is NaN or missing
        return None

    if isinstance(date_value, (pd.Timestamp, datetime)):
        return date_value

    try:
        return pd.to_datetime(date_value)
    except:
        return None

def filter_by_date_range(df, date_column, start_date, end_date):
    if not start_date and not end_date:
        return df

    df = df.copy()
    df[date_column] = df[date_column].apply(parse_date)

    mask = pd.Series([True] * len(df), index=df.index)

    if start_date:
        try:
            start = pd.to_datetime(start_date)
            mask = mask & (df[date_column] >=start)
        except:
            pass

    if end_date:
        try:
            end = pd.to_datetime(end_date)
            mask = mask & (df[date_column] <= end)
        except:
            pass

    return df[mask]



def filter_serials_in_range(df, start_serial, end_serial, start_date=None, end_date=None):
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

        date_column = None
        for col in df.columns:
            col_lower = col.lower()
            if 'Activation_time' in col_lower:
                date_column = col
                break
        df = df.copy()

        df['numeric_serial'] = df[serial_column].astype(str).str.replace('SERIAL_', '', regex=False).str.replace('serial_', '', case=False, regex=False) #remove the SERIAL_ prefix
        df['numeric_serial'] = pd.to_numeric(df['numeric_serial'], errors='coerce')#convert serial numbers to numeric, handling any non-numeric value

        mask = (df['numeric_serial'] >= start) & (df['numeric_serial'] <= end)
        serials_in_range = df[mask] #filter serials in range

        if date_column and (start_date or end_date):
            serials_in_range = filter_by_date_range(serials_in_range, date_column, start_date, end_date) #apply date filter if date column exists and date ranges are provided

        activated_serials = serials_in_range[serials_in_range[msisdn_column].notna() & (serials_in_range[msisdn_column] != '')] #filter activated serials(where servedmsisdn is not blank)

        total_in_range = len(serials_in_range)
        activated_count = len(activated_serials)

        columns_to_return = []
        if serial_column and serial_column in activated_serials.columns:
            columns_to_return.append(serial_column)
        if msisdn_column and msisdn_column in activated_serials.columns:
            columns_to_return.append(msisdn_column)
        if date_column and date_column in activated_serials.columns:
            columns_to_return.append(date_column)

        if not columns_to_return:
            columns_to_return = [col for col in activated_serials.column if col != 'numeric_serial']

        activated_list = []
        if len(activated_serials) > 0:
            return_cols = [col for col in columns_to_return if col != 'numeric_serial']
            activated_list = activated_serials[return_cols].head(100).to_dict('records')

        for item in activated_list:
            if date_column and date_column in item:
                date_val = item[date_column]
                if pd.notna(date_val):
                    try:
                        item[date_column] =  pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    except:
                        item[date_column] = str(date_val)

        return {
            "total_in_range": total_in_range,
            "activated_count": activated_count,
            "activation_rate": round((activated_count / total_in_range * 100), 2) if total_in_range > 0 else 0,
            "activated_serials": activated_list,
            "has_date_column": date_column is not None,
            "date_column_name": date_column
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def filter_by_retailer(df, retailer_msisdn, start_date=None, end_date=None):
    try:
        retailer_column = None
        for col in df.columns:
            col_lower = col.lower()
            if 'retailer_msisdn' in col_lower:
                retailer_column = col
                break

        if retailer_column is None:
            return {"error": "retailer_msisdn column not found"}

        serial_column = None
        for col in df.columns:
            if 'item_serial_number' in col.lower():
                serial_column = col
                break


        msisdn_column = None
        for col in df.columns:
            if 'servedmsisdn' in col.lower():
                msisdn_column = col
                break


        date_column = None
        for col in df.columns:
            col_lower = col.lower()
            if 'activation_time' in col_lower:
                date_column = col
                break

        df = df.copy()
        retailer_mask = df[retailer_column].astype(str).str.contains(str(retailer_msisdn), na=False)
        retailer_serials = df[retailer_mask]

        if date_column and (start_date or end_date):
            retailer_serials = filter_by_date_range(retailer_serials, date_column, start_date, end_date)

        if msisdn_column:
            activated_serials = retailer_serials[retailer_serials[msisdn_column].notna() & (retailer_serials[msisdn_column] != '')]
        else:
            activated_serials = retailer_serials

        total_count = len(retailer_serials)
        activated_count = len(activated_serials)

        columns_to_return = []
        if serial_column and serial_column in activated_serials.columns:
            columns_to_return.append(serial_column)
        if msisdn_column and msisdn_column in activated_serials.columns:
            columns_to_return.append(msisdn_column)
        if retailer_msisdn and retailer_msisdn in activated_serials.columns:
            columns_to_return.append(retailer_column)
        if date_column and date_column in activated_serials.columns:
            columns_to_return.append(date_column)

        if not columns_to_return:
            columns_to_return = activated_serials.columns.tolist()


        activated_list = []
        if len(activated_serials) > 0:
            activated_list = activated_serials[columns_to_return].head(100).to_dict('records')

        for item in activated_list:
            if date_column and date_column in item:
                date_val = item[date_column]
                if pd.notna(date_val):
                    try:
                        item[date_column] = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    except:
                        item[date_column] = str(date_val)

        return {
            "total_count": total_count,
            "activated_count": activated_count,
            "activation_rate": round((activated_count / total_count * 100), 2) if total_count > 0 else 0,
            "activated_serials": activated_list,
            "has_date_column": date_column is not None,
            "date_column_name": date_column
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'current_data.xlsx')
        file.save(filepath)

        try:
            df = load_excel_data(filepath)
            return jsonify({
                "message": "File uploaded successfully",
                "rows": len(df),
                "columns": list(df.columns)
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid data file"}), 400

@app.route('/api/filter', methods=['POST'])
def filter_serials():
    data = request.get_json()

    if not data or 'start_serial' not in data or 'end_serial' not in data:
        return jsonify({"error": "start_serial and end_serial are required"}), 400

    start_serial = data['start_serial']
    end_serial = data['end_serial']
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'current_data.xlsx')
    if not os.path.exists(filepath):
        return jsonify({"error": "No excel file uploaded"}), 400

    try:
        df = load_excel_data(filepath)
        result = filter_serials_in_range(df, start_serial, end_serial, start_date, end_date)

        if "error" in result:
            return jsonify(result), 200
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filter-retailer', methods=['POST'])
def filter_by_retailer_route():
    data = request.get_json()

    if not data or 'retailer_msisdn' not in data:
        return jsonify({"error": "retailer_msisdn is required"}), 400

    retailer_msisdn = data['retailer_msisdn']
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'current_data.xlsx')
    if not os.path.exists(filepath):
        return jsonify({"error": "No excel file uploaded"}), 400

    try:
        df = load_excel_data(filepath)
        result = filter_by_retailer(df, retailer_msisdn, start_date, end_date)

        if "error" in result:
            return jsonify(result), 200

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'current_data.xlsx')

    if os.path.exists(filepath):
        try:
            df = load_excel_data(filepath)
            return jsonify({
                "loaded": True,
                "rows": len(df),
                "last_modified": os.path.getmtime(filepath)
            }), 200
        except Exception as e:
            return jsonify({"loaded": False}), 200

    return jsonify({"loaded": False}), 200



if __name__ == '__main__':
    app.run(debug=True, port=5000)



