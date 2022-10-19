import glob

import rasterio.mask
from pyresample import create_area_def
from satpy.scene import Scene
from shapely.geometry import box


def process_msg_data(data_file, composite_ids, base_dir):
    file_name = glob.glob(data_file)
    scn = Scene(reader="seviri_l1b_native", filenames=file_name)

    scn.load(composite_ids, upper_right_corner="NE")

    world4326 = create_area_def("world4326", projection=4326, resolution=0.035, area_extent=[-180, -90, 180, 90])

    resampled = scn.resample(world4326)

    resampled.save_datasets(filename="{name}.tif", base_dir=base_dir)


def clip_to_extent(extent, infile, outfile):
    bounds_polygon = box(extent[0], extent[1], extent[2], extent[3])

    with rasterio.open(infile) as src:
        out_image, out_transform = rasterio.mask.mask(src, [bounds_polygon], crop=True)
        out_meta = src.meta

        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        with rasterio.open(outfile, "w", **out_meta) as dest:
            dest.write(out_image)

    return outfile
