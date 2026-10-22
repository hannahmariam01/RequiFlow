const users = [];
let nextId = 1;

class UserMock {
  constructor(data) {
    this._id = (nextId++).toString();
    this.name = data.name;
    this.organization = data.organization;
    this.email = data.email;
    this.password = data.password;
    this.isVerified = data.isVerified || false;
    this.verificationToken = data.verificationToken;
  }

  static async findOne(query) {
    if (query.email) {
      return users.find(u => u.email === query.email) || null;
    }
    if (query.verificationToken) {
      return users.find(u => u.verificationToken === query.verificationToken) || null;
    }
    return null;
  }

  async save() {
    const existingIdx = users.findIndex(u => u._id === this._id);
    if (existingIdx !== -1) {
      users[existingIdx] = this;
    } else {
      users.push(this);
    }
    return this;
  }

  get id() {
    return this._id;
  }
}

export default UserMock;
