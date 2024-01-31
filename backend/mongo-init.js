db.createUser({
    user: "dev_user",
    pwd: "dev_pass",
    roles: [{ role: "readWrite", db: "ion"  }]
});
db.createCollection('patients', { capped: false });

db = db.getSiblingDB('test');
db.createUser({
    user: "dev_user",
    pwd: "dev_pass",
    roles: [{ role: "readWrite", db: "ion"  }]
});
db.createCollection('patients', { capped: false });