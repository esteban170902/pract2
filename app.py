from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/database_name'
db = SQLAlchemy(app)

# Definir el modelo de la tabla 'directories'
class Directory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    emails = db.Column(db.ARRAY(db.String), nullable=False)

    def json(self):
        return {'id': self.id,'name': self.name, 'emails': self.emails}

db.create_all()

# Ruta para obtener el estado del servicio
@app.route("/status/", methods=["GET"])
def status():
    return jsonify("pong")

# Ruta para obtener el listado de objetos
@app.route("/directories/", methods=["GET"])
def get_directories():
    # Obtener los parámetros de paginación (opcional)
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    # Calcular el índice inicial y final de la página
    start = (page - 1) * page_size
    end = start + page_size
    # Obtener el total de registros y la página correspondiente utilizando la base de datos
    count = Directory.query.count()
    results = Directory.query.offset(start).limit(page_size).all()
    # Construir la respuesta con el conteo, los links y los resultados
    response = {
        "count": count,
        "next": f"/directories/?page={page + 1}&page_size={page_size}" if end < count else None,
        "previous": f"/directories/?page={page - 1}&page_size={page_size}" if start > 0 else None,
        "results": [directory_to_dict(directory) for directory in results]
    }
    return jsonify(response)

# Ruta para crear un objeto
@app.route("/directories/", methods=["POST"])
def create_object():
    # Obtener los datos del request
    data = request.get_json()
    # Validar que los datos sean un objeto válido
    if not validate_object(data):
        abort(400) # Bad request
    # Crear un nuevo objeto Directory
    directory = Directory(name=data["name"], emails=data["emails"])
    # Agregar el objeto a la base de datos
    db.session.add(directory)
    db.session.commit()
    # Devolver el objeto creado con código 201 (Created)
    return jsonify(directory_to_dict(directory)), 201

# Ruta para obtener un objeto por id
@app.route("/directories/<int:id>/", methods=["GET"])
def get_object_by_id(id):
    # Obtener el objeto por id utilizando la base de datos
    directory = Directory.query.get(id)
    # Si no existe, devolver código 404 (Not found)
    if not directory:
        abort(404)
    # Si existe, devolver el objeto con código 200 (OK)
    return jsonify(directory_to_dict(directory))

# Función auxiliar para convertir un objeto Directory en un diccionario
def directory_to_dict(directory):
    return {
        "id": directory.id,
        "name": directory.name,
        "emails": directory.emails
    }

# Función auxiliar para validar un objeto
def validate_object(obj):
    if not isinstance(obj, dict):
        return False
    if not "name" in obj or not isinstance(obj["name"], str):
        return False
    if not "emails" in obj or not isinstance(obj["emails"], list):
        return False
    for email in obj["emails"]:
        if not isinstance(email, str):
            return False
    return True

if __name__ == '__main__':
    app.run()

# Ruta para actualizar parcialmente un objeto por id
@app.route("/directories/<int:id>/", methods=["PATCH"])
def patch_object_by_id(id):
    # Obtener el objeto por id utilizando la base de datos
    directory = Directory.query.get(id)
    # Si no existe, devolver código 404 (Not found)
    if not directory:
        abort(404)
    # Obtener los datos del request
    data = request.get_json()
    # Validar que los datos sean un diccionario
    if not isinstance(data, dict):
        abort(400) # Bad request
    # Actualizar solo los campos que estén en el request
    if "name" in data and isinstance(data["name"], str):
        directory.name = data["name"]
    if "emails" in data and isinstance(data["emails"], list):
        for email in data["emails"]:
            if not isinstance(email, str):
                abort(400) # Bad request
        directory.emails = data["emails"]
    # Guardar los cambios en la base de datos
    db.session.commit()
    # Devolver el objeto actualizado con código 200 (OK)
    return jsonify(directory_to_dict(directory))

# Ruta para eliminar un objeto por id
@app.route("/directories/<int:id>/", methods=["DELETE"])
def delete_object_by_id(id):
    # Obtener el objeto por id utilizando la base de datos
    directory = Directory.query.get(id)
    # Si no existe, devolver código 404 (Not found)
    if not directory:
        abort(404)
    # Eliminar el objeto de la base de datos
    db.session.delete(directory)
    # Guardar los cambios en la base de datos
    db.session.commit()
    # Devolver código 204 (No content)
    return "", 204