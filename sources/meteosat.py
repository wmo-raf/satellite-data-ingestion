import json
import os
import pathlib
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta

from iso8601 import parse_date

from utils.eumdacapi import EumdacApi
from utils.fs import atomic_write

import subprocess
from utils.conversion import process_msg_data, clip_to_extent

DATASET = {
    "collection": "EO:EUM:DAT:MSG:HRSEVIRI",
    "composites": {
        "natural_color_with_night_ir_hires": {"export_bands": [1, 2, 3]},
        "ir108_3d": {"export_bands": [1]}
    }
}


class MeteosatSource(object):
    name = "meteosat"

    def __init__(self, consumer_key, consumer_secret, state_directory, output_dir):
        self.api = EumdacApi(consumer_key=consumer_key, consumer_secret=consumer_secret)
        self.state_file = None
        self.state_directory = state_directory
        self.extent = [-25.3605509351584004, -34.8219979618462006, 63.4957562687202994, 37.3404070787983002]
        self.output_dir = output_dir
        self.composites = DATASET.get("composites")

        self.init_state()

    def init_state(self):

        pathlib.Path(self.state_directory).mkdir(parents=True, exist_ok=True)

        file_name = f"{self.name}.json"

        state_file = os.path.join(self.state_directory, file_name)

        if not os.path.exists(state_file):
            pathlib.Path(state_file).touch(exist_ok=True)
            # write empty dict
            with open(state_file, 'w') as f:
                json.dump({}, f)

        self.state_file = state_file

    def read_state(self):
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {}
        return state

    def update_state(self, new_date):
        new_state = {
            "date": new_date.replace(second=0).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "last_updated": datetime.now().isoformat()
        }

        json_string = json.dumps(new_state)

        atomic_write(json_string, self.state_file)

    def update(self):
        current_state = self.read_state()
        date = current_state.get("date")
        collection = DATASET.get("collection")

        if date:
            # increment by 15 minutes
            dt = parse_date(date) + timedelta(minutes=15)
        else:
            # get current hour
            dt = datetime.now().replace(minute=0, second=0, microsecond=0)

        data_id = self.check_should_update(collection, dt)

        if data_id:
            self.download_and_process_data(collection, data_id, dt)

    def check_should_update(self, collection, dt):
        start_dt = dt - timedelta(minutes=30)
        end_dt = dt + timedelta(minutes=30)

        products = self.api.search_collection(collection, start_dt.isoformat(), end_dt.isoformat())

        data_dt = dt.replace(second=0).strftime('%Y-%m-%dT%H:%M:%SZ')

        data_id = None

        if products:
            for product in products:
                date = product.get("date").strftime('%Y-%m-%dT%H:%M:%SZ')
                if date == data_dt:
                    data_id = product.get("identifier")
                    break

        return data_id

    def download_and_process_data(self, collection, data_id, dt):
        temp_dir = tempfile.mkdtemp()

        file_name_zip = os.path.join(temp_dir, data_id + ".zip")

        try:
            print("Started Downloading...")
            with self.api.open(collection, data_id) as f_src, open(file_name_zip, mode='wb') as f_dst:
                shutil.copyfileobj(f_src, f_dst)

            with zipfile.ZipFile(file_name_zip, "r") as zf:
                zf.extractall(temp_dir)

            # delete zip file
            os.unlink(file_name_zip)

            file_name = os.path.join(temp_dir, data_id + ".nat")
            print("Done Downloading...")

            composite_ids = list(self.composites.keys())

            print("Starting processing")
            process_msg_data(data_file=file_name, composite_ids=composite_ids, base_dir=temp_dir)

            for layer in composite_ids:
                layer_name = f"{layer}.tif"

                infile = os.path.join(temp_dir, layer_name)

                temp_out_file_dir = os.path.join(temp_dir, layer)

                pathlib.Path(temp_out_file_dir).mkdir(parents=True, exist_ok=True)

                date_str = dt.strftime('%Y-%m-%dT%H:%M:00.000Z')

                temp_out_file_name = f"{layer}_{date_str}.tif"

                temp_outfile = os.path.join(temp_out_file_dir, temp_out_file_name)

                clip_to_extent(self.extent, infile, temp_outfile)

                out_file_dir = os.path.join(self.output_dir, layer)
                pathlib.Path(out_file_dir).mkdir(parents=True, exist_ok=True)

                export_bands = self.composites.get(layer, {}).get("export_bands")

                if export_bands:
                    for band in export_bands:
                        out_file_name = f"band{band}_{layer}_{date_str}.tif"
                        outfile = os.path.join(out_file_dir, out_file_name)
                        args = ["gdal_translate", "-b", f"{band}", temp_outfile, outfile]
                        subprocess.call(args)

            # cleanup tempdir
            shutil.rmtree(temp_dir, ignore_errors=True)

            self.update_state(dt)

        except Exception as e:
            # shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    @staticmethod
    def get_default_start_date():
        dt = datetime(2022, 10, 18)
        return dt
