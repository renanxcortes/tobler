"""
Area Weighted Interpolation

"""

import numpy as np
import geopandas as gpd

def area_table(source_df, target_df):
    """
    Calculate area of each source feature (row) intersecting with each target feature (column)

    Parameters
    ----------

    source_df: geopandas GeoDataFrame with geometry column of polygon type

    source_df: geopandas GeoDataFrame with geometry column of polygon type

    Returns
    -------
    table: array
           area mapping reporting intersection of target polygon i with source polygon j for all polygons i in source_df and j in target_df


    Notes
    -----
    The assumption is both dataframes have the same coordinate reference system.


    Todo
    ----

    - add warnings for non-exhaustion across rows/columns


    """
    n_s = source_df.shape[0]
    n_t = target_df.shape[0]
    _left = np.arange(n_s)
    _right = np.arange(n_t)
    table = np.zeros((n_s, n_t))
    # assume each layer is planar enforced
    source_df['_left'] = _left  # create temporary index for union
    target_df['_right'] = _right # create temporary index for union
    res_union = gpd.overlay(source_df, target_df, how='union')
    for idx, row in res_union.iterrows():
        i = row['_left']
        j = row['_right']
        #print(idx, i, j)
        if not np.isnan([i, j]).any():
            #print('ok',i,j)
            table[int(i-1), int(j-1)] = row['geometry'].area
    del source_df['_left']  # remove temporary index
    del target_df['_right'] # remove temporary index
    return table


def area_extensive(source_df, target_df, att_name, table=None):
    """
    Interpolate extensive attribute values from source features to target features

    Parameters
    ----------

    source_df: geopandas GeoDataFrame with geometry column of polygon type

    source_df: geopandas GeoDataFrame with geometry column of polygon type

    att_name: string
              column name in source_df to interpolate over target_df 


    table: array (optional)
           area mapping reporting intersection of target polygon i with source polygon j for all polygons i in source_df and j in target_df

    Notes
    -----
    The assumption is both dataframes have the same coordinate reference system.


    Estimate at target polygon j:

    v_j = \sum_i v_i w_{i,j}

    w_{i,j} = a_{i,j} / \sum_k a_{i,k}





    """
    att = source_df[att_name]
    if table is None:
        table = area_table(source_df, target_df)
    row_sum = table.sum(axis=1)
    row_sum = row_sum + (row_sum == 0)
    weights = np.dot(np.diag(1/row_sum), table)
    print(table.shape, att.shape, weights.shape)
    estimates = np.dot(np.diag(att), weights)
    return estimates.sum(axis=0)


def area_intensive(source_df, target_df, att_name, table=None):
    """
    Interpolate intensive attribute values from source features to target features

    Parameters
    ----------

    source_df: geopandas GeoDataFrame with geometry column of polygon type

    source_df: geopandas GeoDataFrame with geometry column of polygon type

    att_name: string
              column name in source_df to interpolate over target_df 


    table: array (optional)
           area mapping reporting intersection of target polygon i with source polygon j for all polygons i in source_df and j in target_df

    Notes
    -----
    The assumption is both dataframes have the same coordinate reference system.

    Estimate at target polygon j:

    v_j = \sum_i v_i w_{i,j}

    w_{i,j} = a_{i,j} / \sum_k a_{k,j}




    """
    att = source_df[att_name]
    if table is None:
        table = area_table(source_df, target_df)
    area = table.sum(axis=0)
    den = np.diag(1./ (area + (area == 0)))
    weights = np.dot(table, den)
    vals = att.values
    vals.shape = (len(vals), 1)
    return  (vals * weights).sum(axis=0)

