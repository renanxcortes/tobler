from tobler.vectorized_raster_interpolation import *
from tobler.data import *

import rasterio
import unittest
import libpysal

import geopandas as gpd
import numpy as np

from shapely.geometry import Polygon
from shapely.ops import cascaded_union

import xgboost as xgb
import shap

class VectorizedRasterInterpolation_Tester(unittest.TestCase):
    def test_VectorizedRasterInterpolation(self):
        local_raster_path = fetch_quilt_path('nlcd_2011')
        nlcd_raster = rasterio.open(local_raster_path)
        
        s_map = gpd.read_file(libpysal.examples.get_path("sacramentot2.shp"))
        df = s_map[['geometry', 'TOT_POP']]
        df.crs = {'init': 'epsg:4326'}
        
        # Shrinking the spatial extent
        df = df[((df.centroid.x < -121.4) & (df.centroid.x > -121.5) & (df.centroid.y > 38.5) & (df.centroid.y < 38.8))]
        df = df.set_geometry('geometry')
        
        weights = return_weights_from_regression(df, local_raster_path, 'TOT_POP')
        
        correspondence_table = create_non_zero_population_by_pixels_locations(df, nlcd_raster, 'TOT_POP', weights)
        
        boundary = gpd.GeoSeries(cascaded_union(df.geometry)).buffer(0.001) # The 'buffer' method prevents some unusual points inside the state
        df_region_pre = gpd.GeoDataFrame(gpd.GeoSeries(boundary))
        df_region = df_region_pre.rename(columns={0:'geometry'}).set_geometry('geometry')
        
        low_left  = -121.6
        low_right = -121.3
        up_left = 38.4
        up_right = 39
        
        thickness = 15
        
        # This snippet was inspired in https://github.com/pysal/libpysal/blob/aa7882e7877b962f4269ea86a612dfc58152e5c6/libpysal/weights/user.py#L95
        aux = list()
        for i in np.linspace(low_left, low_right, num = thickness):
                for j in np.linspace(up_left, up_right, num = thickness):
                    
                    # Each width 'jump' must be at the same order of the grid constructed
                    ll = i, j
                    ul = i, j + np.diff(np.linspace(up_left, up_right, num = thickness))[0]
                    ur = i + np.diff(np.linspace(low_left, low_right, num = thickness))[0], j + np.diff(np.linspace(up_left, up_right, num = thickness))[0]
                    lr = i + np.diff(np.linspace(low_left, low_right, num = thickness))[0], j
                    aux.append(Polygon([ll, ul, ur, lr, ll]))
                    
        polys2 = gpd.GeoSeries(aux)
        
        envgdf = gpd.GeoDataFrame(polys2)
        envgdf_final = envgdf.rename(columns={0:'geometry'}).set_geometry('geometry')
        
        res_union = gpd.overlay(df_region, envgdf_final, how='intersection')
        res_union.crs = df.crs
        
        interpolated = calculate_interpolated_population_from_correspondence_table(res_union, nlcd_raster, correspondence_table)
        
        x = np.array(interpolated['interpolated_population'])
        x.sort()
        
        np.testing.assert_almost_equal(x, np.array([2.29409707e+01, 6.48706970e+01, 1.21688696e+03, 1.83378287e+03,
       1.87042079e+03, 1.90379325e+03, 2.25049982e+03, 3.21650854e+03,
       3.41236645e+03, 3.71181098e+03, 5.12532031e+03, 5.75600935e+03,
       8.63080789e+03, 9.26963356e+03, 1.00591807e+04, 1.04378577e+04,
       1.29541218e+04, 1.56270494e+04, 1.89447344e+04, 1.91294133e+04,
       1.93945973e+04, 2.06785383e+04, 2.15440941e+04, 2.29075806e+04,
       2.30862412e+04, 2.49861096e+04, 2.97869188e+04, 2.99332151e+04,
       3.12133550e+04, 3.18697373e+04, 3.19341907e+04, 3.37013110e+04,
       4.10443313e+04, 4.49694860e+04]), decimal = 3)

    
    def test_VectorizedRasterInterpolation_XGBoost(self):
        local_raster_path = fetch_quilt_path('nlcd_2011')
        nlcd_raster = rasterio.open(local_raster_path)
        
        s_map = gpd.read_file(libpysal.examples.get_path("sacramentot2.shp"))
        df = s_map[['geometry', 'TOT_POP']]
        df.crs = {'init': 'epsg:4326'}
        
        # Shrinking the spatial extent
        df = df[((df.centroid.x < -121.4) & (df.centroid.x > -121.5) & (df.centroid.y > 38.5) & (df.centroid.y < 38.8))]
        df = df.set_geometry('geometry')
        
        weights = return_weights_from_xgboost(df, local_raster_path, 'TOT_POP')
        
        correspondence_table = create_non_zero_population_by_pixels_locations(df, nlcd_raster, 'TOT_POP', weights)
        
        boundary = gpd.GeoSeries(cascaded_union(df.geometry)).buffer(0.001) # The 'buffer' method prevents some unusual points inside the state
        df_region_pre = gpd.GeoDataFrame(gpd.GeoSeries(boundary))
        df_region = df_region_pre.rename(columns={0:'geometry'}).set_geometry('geometry')
        
        low_left  = -121.6
        low_right = -121.3
        up_left = 38.4
        up_right = 39
        
        thickness = 15
        
        # This snippet was inspired in https://github.com/pysal/libpysal/blob/aa7882e7877b962f4269ea86a612dfc58152e5c6/libpysal/weights/user.py#L95
        aux = list()
        for i in np.linspace(low_left, low_right, num = thickness):
                for j in np.linspace(up_left, up_right, num = thickness):
                    
                    # Each width 'jump' must be at the same order of the grid constructed
                    ll = i, j
                    ul = i, j + np.diff(np.linspace(up_left, up_right, num = thickness))[0]
                    ur = i + np.diff(np.linspace(low_left, low_right, num = thickness))[0], j + np.diff(np.linspace(up_left, up_right, num = thickness))[0]
                    lr = i + np.diff(np.linspace(low_left, low_right, num = thickness))[0], j
                    aux.append(Polygon([ll, ul, ur, lr, ll]))
                    
        polys2 = gpd.GeoSeries(aux)
        
        envgdf = gpd.GeoDataFrame(polys2)
        envgdf_final = envgdf.rename(columns={0:'geometry'}).set_geometry('geometry')
        
        res_union = gpd.overlay(df_region, envgdf_final, how='intersection')
        res_union.crs = df.crs
        
        interpolated = calculate_interpolated_population_from_correspondence_table(res_union, nlcd_raster, correspondence_table)
        
        x = np.array(interpolated['interpolated_population'])
        x.sort()
        
        np.testing.assert_almost_equal(x, np.array([2.53672449e+01, 6.54430222e+01, 1.25262612e+03, 1.74926641e+03,
       1.75978072e+03, 2.03962119e+03, 2.31218306e+03, 3.15827664e+03,
       3.53996470e+03, 3.90501280e+03, 5.04094373e+03, 5.75976246e+03,
       8.55500679e+03, 9.31109828e+03, 1.00484437e+04, 1.03374813e+04,
       1.29501733e+04, 1.57427949e+04, 1.90356030e+04, 1.90490460e+04,
       1.93900769e+04, 2.07701666e+04, 2.14429988e+04, 2.30598353e+04,
       2.30827471e+04, 2.50598443e+04, 2.98398344e+04, 3.00747744e+04,
       3.14157039e+04, 3.14855934e+04, 3.17182056e+04, 3.38859914e+04,
       4.08898548e+04, 4.50842888e+04]), decimal = 3)

    
    
    def test_VectorizedRasterInterpolation_TUNED_XGBoost(self):
        local_raster_path = fetch_quilt_path('nlcd_2011')
        nlcd_raster = rasterio.open(local_raster_path)
        
        s_map = gpd.read_file(libpysal.examples.get_path("sacramentot2.shp"))
        df = s_map[['geometry', 'TOT_POP']]
        df.crs = {'init': 'epsg:4326'}
        
        # Shrinking the spatial extent
        df = df[((df.centroid.x < -121.4) & (df.centroid.x > -121.5) & (df.centroid.y > 38.5) & (df.centroid.y < 38.8))]
        df = df.set_geometry('geometry')
        
        weights = return_weights_from_xgboost(df, local_raster_path, 'TOT_POP', tuned_xgb=True, gbm_hyperparam_grid={"learning_rate": [0.01]})
        
        correspondence_table = create_non_zero_population_by_pixels_locations(df, nlcd_raster, 'TOT_POP', weights)
        
        boundary = gpd.GeoSeries(cascaded_union(df.geometry)).buffer(0.001) # The 'buffer' method prevents some unusual points inside the state
        df_region_pre = gpd.GeoDataFrame(gpd.GeoSeries(boundary))
        df_region = df_region_pre.rename(columns={0:'geometry'}).set_geometry('geometry')
        
        low_left  = -121.6
        low_right = -121.3
        up_left = 38.4
        up_right = 39
        
        thickness = 15
        
        # This snippet was inspired in https://github.com/pysal/libpysal/blob/aa7882e7877b962f4269ea86a612dfc58152e5c6/libpysal/weights/user.py#L95
        aux = list()
        for i in np.linspace(low_left, low_right, num = thickness):
                for j in np.linspace(up_left, up_right, num = thickness):
                    
                    # Each width 'jump' must be at the same order of the grid constructed
                    ll = i, j
                    ul = i, j + np.diff(np.linspace(up_left, up_right, num = thickness))[0]
                    ur = i + np.diff(np.linspace(low_left, low_right, num = thickness))[0], j + np.diff(np.linspace(up_left, up_right, num = thickness))[0]
                    lr = i + np.diff(np.linspace(low_left, low_right, num = thickness))[0], j
                    aux.append(Polygon([ll, ul, ur, lr, ll]))
                    
        polys2 = gpd.GeoSeries(aux)
        
        envgdf = gpd.GeoDataFrame(polys2)
        envgdf_final = envgdf.rename(columns={0:'geometry'}).set_geometry('geometry')
        
        res_union = gpd.overlay(df_region, envgdf_final, how='intersection')
        res_union.crs = df.crs
        
        interpolated = calculate_interpolated_population_from_correspondence_table(res_union, nlcd_raster, correspondence_table)
        
        x = np.array(interpolated['interpolated_population'])
        x.sort()
        
        np.testing.assert_almost_equal(x, np.array([7.94275201e+00, 3.23305161e+01, 1.29817102e+03, 1.63662479e+03,
       1.69880785e+03, 2.58954372e+03, 2.72008993e+03, 2.83888406e+03,
       3.88606112e+03, 4.74542953e+03, 5.04243256e+03, 5.71170529e+03,
       8.09424356e+03, 8.89014392e+03, 9.31156523e+03, 1.03061387e+04,
       1.31094584e+04, 1.70605442e+04, 1.83368644e+04, 1.84115205e+04,
       1.92882217e+04, 2.15500526e+04, 2.15672205e+04, 2.33767047e+04,
       2.34402726e+04, 2.56923320e+04, 2.94053560e+04, 3.06803910e+04,
       3.08641646e+04, 3.13994173e+04, 3.20735589e+04, 3.45226403e+04,
       4.08243883e+04, 4.47745432e+04]), decimal = 3)
if __name__ == '__main__':
    unittest.main()
