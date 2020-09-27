import tenseal as ts
import numpy as np
import torch
from hesystem.client import retrieve_data
# parameters
poly_mod_degree = 8192
coeff_mod_bit_sizes = [40, 21, 21, 21, 21, 21, 21, 40]
# create TenSEALContext
ctx_training = ts.context(ts.SCHEME_TYPE.CKKS, poly_mod_degree, -1, coeff_mod_bit_sizes)
ctx_training.global_scale = 2 ** 21
ctx_training.generate_galois_keys()

ckks_vec = ts.ckks_vector(ctx_training, [1,2,3,4])
#ctx_client = ctx_training.make_context_public()
random_array = [1] * 5
ckks_vec = ts.ckks_vector(ctx_training, random_array)
size = ckks_vec.size()
data, ctx = retrieve_data('nico', 'http://127.0.0.1:5000/restaurants/test')


'''
CREATE TABLE  rucs  (
   numero_ruc  bigint DEFAULT NULL,
   razon_social   varchar,
   nombre_comercial   varchar,
   estado_contribuyente  char(10) DEFAULT NULL,
   clase_contribuyente  char(8) DEFAULT NULL,
   fecha_inicio_actividades  varchar DEFAULT NULL,
   fecha_actualizacion  varchar DEFAULT NULL,
   fecha_suspension_definitiva  varchar DEFAULT NULL,
   fecha_reinicio_actividades  varchar DEFAULT NULL,
   obligado  char(1) DEFAULT NULL,
   tipo_contribuyente   varchar,
   numero_establecimiento  int DEFAULT NULL,
   nombre_fantasia_comercial   varchar,
   calle   varchar,
   numero   varchar,
   interseccion   varchar,
   estado_establecimiento  char(3) DEFAULT NULL,
   descripcion_provincia   varchar,
   descripcion_canton   varchar,
   descripcion_parroquia   varchar,
   codigo_ciiu  char(10) DEFAULT NULL,
   actividad_economica  int DEFAULT NULL,
   lat   float DEFAULT NULL,
   lon   float DEFAULT NULL,
   nombre_local   varchar,
   total_establecimientos  int DEFAULT NULL,
   duracion  int DEFAULT NULL,
   business_size   float DEFAULT NULL,
   DENSIDAD_P  float DEFAULT NULL,
   PODER_ADQU  float DEFAULT NULL,
   categoria_ARROZ  float DEFAULT NULL,
   categoria_BAR  float DEFAULT NULL,
   categoria_BAZAR  float DEFAULT NULL,
   categoria_CAFETERIA  float DEFAULT NULL,
   categoria_CARNE  float DEFAULT NULL,
   categoria_CARPINTERIA  float DEFAULT NULL,
   categoria_CALZADO  float DEFAULT NULL,
   categoria_COMBUSTIBLE  float DEFAULT NULL,
   categoria_CYBERCAFES  float DEFAULT NULL,
   categoria_ELECTRODOMESTICOS  float DEFAULT NULL,
   categoria_FARMACIA  float DEFAULT NULL,
   categoria_FERRETERIA  float DEFAULT NULL,
   categoria_FLORES  float DEFAULT NULL,
   categoria_FRUTAS_Y_LEGUMBRES  float DEFAULT NULL,
   categoria_HELADOS  float DEFAULT NULL,
   categoria_HUEVOS  float DEFAULT NULL,
   categoria_JUEGOS_Y_JUGUETES  float DEFAULT NULL,
   categoria_LACTEOS  float DEFAULT NULL,
   categoria_LICORERIA  float DEFAULT NULL,
   categoria_LIMPIEZA  float DEFAULT NULL,
   categoria_MECANICA  float DEFAULT NULL,
   categoria_PANADERIA  float DEFAULT NULL,
   categoria_PAPELERIA  float DEFAULT NULL,
   categoria_PELUQUERIA  float DEFAULT NULL,
   categoria_PERFUMERIA  float DEFAULT NULL,
   categoria_PICANTERIA  float DEFAULT NULL,
   categoria_PINTURA  float DEFAULT NULL,
   categoria_RESTAURANTE  float DEFAULT NULL,
   categoria_ROPA  float DEFAULT NULL,
   categoria_SUPERMERCADO  float DEFAULT NULL,
   categoria_TIENDA  float DEFAULT NULL
);

SELECT duracion, business_size, DENSIDAD_P, PODER_ADQU, categoria_TIENDA, categoria_RESTAURANTE, lat, lon
FROM RUCs r INNER JOIN businesscategory b on CAST(r.actividad_economica as INT )=b.id_actividad
WHERE b.business_category = 'RESTAURANTE'
'''
