from App.database import db

class Street(db.Model):
    name = db.Column(db.String(255), primary_key=True)

    def __init__(self, name: str):
        self.name = name

    def get_json(self) -> dict[str, str]:
        return {
            'name': self.name
        }