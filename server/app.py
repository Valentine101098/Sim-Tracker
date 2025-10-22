from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
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


def parse_data(date_value):
    if pd.isna(date_value):
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

    df[date_column] = df[date_column].apply(parse_data)

    mask = pd.Series([True] * len(df))

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

        df[serial_column] = pd.to_numeric(df[serial_column], errors='coerce') #convert serial numbers to numeric, handling any non-numeric value

        mask = (df[serial_column] >= start) & (df[serial_column] <= end)
        serials_in_range = mask[df] #filter serials in range

        if date_column and (start_date or end_date):
            serials_in_range = filter_by_date_range(serials_in_range, date_column, start_date, end_date) #apply date filter if date column exists and date ranges are provided

        activated_serials = serials_in_range[serials_in_range[msisdn_column].notna() & (serials_in_range[msisdn_column] != '')] #filter activated serials(where servedmsisdn is not blank)

        total_in_range = len(serials_in_range)
        activated_count = len(activated_serials)

        columns_to_return = [serial_column, msisdn_column]
        if date_column:
            columns_to_return.append[date_column]

        activated_list = activated_serials[columns_to_return].head(100).to_dict('records')

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
            "activation_rate": ((activated_count / total_in_range * 100), 2) if total_in_range > 0 else 0,
            "activated_serials": activated_list,
            "has_date_column": date_column is not None,
            "date_column_name": date_column
        }

    except Exception as e:
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
            if 'Activation_time' in col_lower:
                date_column = col
                break

        retailer_mask = df[retailer_column].astype(str).str.contains(str(retailer_msisdn), na=False)
        retailer_serials = df[retailer_mask]

        if date_column and (start_date or end_date):
            retailer_serials = filter_by_date_range(retailer_serials, date_column, start_date, end_date)

        if msisdn_column:
            activated_serials = [retailer_serials[msisdn_column].notna() & (retailer_serials[msisdn_column] != '')]
        else:
            activated_serials = retailer_serials

        total_count = len(retailer_serials)
        activated_count = len(activated_serials)

        columns_to_return = []
        if serial_column:
            columns_to_return.append(serial_column)
        if msisdn_column:
            columns_to_return.append(msisdn_column)
        if retailer_column:
            columns_to_return.append(retailer_column)
        if date_column:
            columns_to_return.append(date_column)

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
        return {"error": str(e)}


if __name__ == '__main__':
    app.run(debug=True, port=5000)

