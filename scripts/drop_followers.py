import xmlrpc.client
import argparse

# Argumentos
parser = argparse.ArgumentParser(description='Eliminar registros de mail.followers por partner_ids.')
parser.add_argument('--model', type=str, required=True, help='Modelo a afectar (ej. mail.followers)')
parser.add_argument('--partner_ids', type=str, required=True, help='IDs separados por coma de res.partner')
parser.add_argument('--url', type=str, required=True, help='URL de Odoo (ej. http://localhost:8069)')
parser.add_argument('--db', type=str, required=True, help='Nombre de la base de datos')
parser.add_argument('--user', type=str, required=True, help='Nombre de usuario')
parser.add_argument('--password', type=str, required=True, help='Contraseña del usuario')

args = parser.parse_args()

# Conexión
common = xmlrpc.client.ServerProxy(f'{args.url}/xmlrpc/2/common')
uid = common.authenticate(args.db, args.user, args.password, {})

models = xmlrpc.client.ServerProxy(f'{args.url}/xmlrpc/2/object')

# Convertimos partner_ids a lista de enteros
partner_ids = [int(pid.strip()) for pid in args.partner_ids.split(',') if pid.strip().isdigit()]

# Buscar registros de mail.followers con esos partner_ids
ids_to_delete = models.execute_kw(
    args.db, uid, args.password,
    'mail.followers', 'search',
    [[
        ['partner_id', 'in', partner_ids],
        ['res_model', '=', args.model] 
    ]]
)

# Eliminar si hay resultados
if ids_to_delete:
    try:
        result = models.execute_kw(
            args.db, uid, args.password,
            'mail.followers', 'unlink',
            [ids_to_delete]
        )
        if result:
            print(f"Se eliminaron {len(ids_to_delete)} registros de mail.followers.")
        else:
            print("La operación 'unlink' se ejecutó pero no se eliminaron registros (devuelve False).")
    except xmlrpc.client.Fault as e:
        print("Error al intentar eliminar los registros:")
        print(e)
else:
    print('No se encontraron registros para eliminar.')
