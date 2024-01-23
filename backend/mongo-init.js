db.createUser({
    user: "dev_user",
    pwd: "dev_pass",
    roles: [
        {
            role: "readWrite",
            db: "ion"
        }
    ]
});

db = new Mongo().getDB("ion");
db.createCollection('patients', { capped: false });
