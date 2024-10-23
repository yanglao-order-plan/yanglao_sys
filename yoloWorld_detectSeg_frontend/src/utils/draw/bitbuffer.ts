class BitBuffer {
  buffer: ArrayBuffer;
  view: Uint8Array;
  length: number;
  capacity: number;

  constructor(byteCapacity: number) {
    this.buffer = new ArrayBuffer(byteCapacity);
    this.view = new Uint8Array(this.buffer);
    this.length = 0;
    this.capacity = 8 * byteCapacity;
  }

  static From(buf: ArrayBuffer | number[]): BitBuffer {
    const b = new BitBuffer(0);
    if (Array.isArray(buf)) {
      return b.appendMany(buf);
    }
    b.buffer = buf;
    b.capacity = 8 * buf.byteLength;
    b.length = b.capacity;
    b.view = new Uint8Array(b.buffer);
    return b;
  }

  expand(): void {
    const newSize = Math.max(1024, this.buffer.byteLength * 2);
    const newBuffer = new ArrayBuffer(newSize);
    const newView = new Uint8Array(newBuffer);
    newView.set(this.view, 0);
    this.buffer = newBuffer;
    this.view = newView;
    this.capacity = 8 * newSize;
  }

  appendBit(value: number): void {
    if (!value) {
      this.length++;
      return;
    }
    if (this.length >= this.capacity) {
      this.expand();
    }
    this.view[this.length >> 3] |= 1 << (this.length % 8);
    this.length++;
  }

  append(value: number, cnt: number): void {
    while (this.length + cnt > this.capacity) {
      this.expand();
    }

    if (!value) {
      this.length += cnt;
      return;
    }
    while (cnt > 0) {
      if (this.length % 8 === 0 && cnt >= 8) {
        this.view[this.length >> 3] = 0xff;
        this.length += 8;
        cnt -= 8;
      } else {
        this.view[this.length >> 3] |= 1 << (this.length % 8);
        this.length++;
        cnt--;
      }
    }
  }

  appendRun(len: number): void {
    if (len === 1) {
      this.appendBit(1);
    } else if (len < 16) {
      this.appendBit(0);
      this.appendBit(1);
      this.appendBit(len & 1);
      this.appendBit(len & 2);
      this.appendBit(len & 4);
      this.appendBit(len & 8);
    } else {
      this.append(0, 2);
      while (len > 127) {
        this.appendBit(len & 1);
        this.appendBit(len & 2);
        this.appendBit(len & 4);
        this.appendBit(len & 8);
        this.appendBit(len & 16);
        this.appendBit(len & 32);
        this.appendBit(len & 64);
        this.appendBit(1);
        len = len >> 7;
      }
      this.appendBit(len & 1);
      this.appendBit(len & 2);
      this.appendBit(len & 4);
      this.appendBit(len & 8);
      this.appendBit(len & 16);
      this.appendBit(len & 32);
      this.appendBit(len & 64);
      this.appendBit(0);
    }
  }

  appendMany(arr: number[]): BitBuffer {
    let val = 0;
    arr.forEach((el) => {
      this.append(val, el);
      val = val ? 0 : 1;
    });
    return this;
  }

  readBit(position: number): number {
    return (this.view[position >> 3] & (1 << (position % 8))) ? 1 : 0;
  }

  readRun(position: number): [number, number] {
    if (this.readBit(position++)) {
      return [1, 1];
    }
    if (this.readBit(position++)) {
      return [6,
        (this.readBit(position++) ? 1 : 0) +
        (this.readBit(position++) ? 2 : 0) +
        (this.readBit(position++) ? 4 : 0) +
        (this.readBit(position) ? 8 : 0)
      ];
    }
    let more = false;
    let val = 0;
    let bits = 2;
    let msb = 0;
    do {
      bits += 8;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      if (this.readBit(position++)) { val += (1 << msb); }
      msb++;
      more = this.readBit(position++) ? true : false;
    } while (more);
    return [bits, val];
  }

  toBuffer(): ArrayBuffer {
    return this.buffer.slice(0, (this.length + 7) >> 3);
  }

  Decode(): ArrayBuffer {
    const outBuffer = new BitBuffer(0);

    if (this.readBit(0) || this.readBit(1)) {
      throw new Error('Invalid version');
    }

    let pos = 2;
    let val = this.readBit(pos++);

    if (this.capacity - this.length < 16) {
      this.expand();
    }
    while (pos < this.length) {
      const next = this.readRun(pos);
      if (next[1] === 0) {
        break;
      }
      pos += next[0];
      outBuffer.append(val, next[1]);
      val = val ? 0 : 1;
    }
    return outBuffer.toBuffer();
  }
}

export default BitBuffer;
