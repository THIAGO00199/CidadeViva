import Phaser from "phaser";

export type Citizen = {
  id: number;
  name: string;
  age: number;
  profession: string;
  bio?: string;
  personality?: string;
  core_values?: string[];
  goals?: string[];
  energy?: number;
  hunger?: number;
  mood?: number;
  social_need?: number;
  money?: number;
  current_activity?: string;
  x: number;
  y: number;
  is_player: number;
  alive?: number;
};

type MoveHandler = (x: number, y: number) => void;

export class CityScene extends Phaser.Scene {
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private keys!: Record<string, Phaser.Input.Keyboard.Key>;
  private citizens: Citizen[] = [];
  private sprites = new Map<number, Phaser.GameObjects.Container>();
  private characterSprites = new Map<number, Phaser.GameObjects.Sprite>();
  private walkClock = 0;
  private walkFrame = 1;
  private facing = 0;
  private onSelect: (citizen: Citizen) => void;
  private onMove: MoveHandler;
  private saveClock = 0;

  constructor(onSelect: (citizen: Citizen) => void, onMove: MoveHandler) {
    super("CityScene");
    this.onSelect = onSelect;
    this.onMove = onMove;
  }

  setCitizens(citizens: Citizen[]) {
    this.citizens = citizens;
    if (this.scene.isActive()) this.renderPeople();
    const player = this.citizens.find((citizen) => citizen.is_player);
    const sprite = player ? this.sprites.get(player.id) : undefined;
    if (sprite && this.scene.isActive()) {
      this.cameras.main.startFollow(sprite, true, 0.08, 0.08);
    }
  }

  preload() {
    this.load.spritesheet("citizens", "/assets/citizens.png", {
      frameWidth: 16,
      frameHeight: 24
    });
  }

  create() {
    this.cameras.main.setBackgroundColor("#263d30");
    this.drawTown();
    this.cameras.main.setBounds(0, 0, 1400, 900);
    this.cameras.main.setZoom(1);

    this.cursors = this.input.keyboard!.createCursorKeys();
    this.keys = this.input.keyboard!.addKeys("W,A,S,D") as Record<string, Phaser.Input.Keyboard.Key>;

    this.input.on("pointerdown", (pointer: Phaser.Input.Pointer) => {
      const worldX = pointer.worldX;
      const worldY = pointer.worldY;
      const hit = this.citizens.find((citizen) => {
        const dx = citizen.x * 32 - worldX;
        const dy = citizen.y * 32 - worldY;
        return Math.abs(dx) < 19 && Math.abs(dy) < 25;
      });
      if (hit && !hit.is_player) this.onSelect(hit);
    });

    this.renderPeople();
    const player = this.citizens.find((citizen) => citizen.is_player);
    if (player) {
      const sprite = this.sprites.get(player.id);
      if (sprite) this.cameras.main.startFollow(sprite, true, 0.08, 0.08);
    }
  }

  private drawTown() {
    const ground = this.add.graphics();
    for (let y = 0; y < 900; y += 32) {
      for (let x = 0; x < 1400; x += 32) {
        const tile = ((x / 32 + y / 32) % 2 === 0) ? 0x35533c : 0x304b37;
        ground.fillStyle(tile, 1);
        ground.fillRect(x, y, 32, 32);
      }
    }

    // Praça e caminhos principais.
    ground.fillStyle(0xb8a47d, 1);
    ground.fillRect(0, 390, 1400, 76);
    ground.fillRect(650, 0, 82, 900);
    ground.fillStyle(0xd2bd91, 1);
    ground.fillRect(585, 390, 210, 76);

    // Lago e parque.
    ground.fillStyle(0x416d78, 1);
    ground.fillEllipse(1120, 675, 230, 150);
    ground.fillStyle(0x8aab83, 1);
    ground.fillEllipse(1120, 675, 194, 116);

    // Construções.
    this.building(145, 125, 185, 125, "MORADIAS", 0x8c795c, 0x654b3a);
    this.building(440, 125, 170, 125, "ESCOLA", 0x9a865f, 0x70543b);
    this.building(830, 125, 190, 125, "UNIDADE DE SAÚDE", 0x9caa91, 0x52624c);
    this.building(1160, 125, 170, 125, "ATELIÊ", 0x9a7b68, 0x62493f);
    this.building(145, 600, 190, 130, "MERCADO", 0x987b58, 0x654832);
    this.building(465, 600, 175, 130, "OFICINAS", 0x8c795c, 0x654b3a);
    this.building(825, 600, 170, 130, "BIBLIOTECA", 0x8d8e71, 0x555d45);

    // Árvores distribuídas pelas bordas e pelo parque.
    const trees = [
      [70, 80], [375, 80], [700, 80], [1080, 80], [1350, 250],
      [65, 520], [375, 520], [700, 520], [1080, 520], [1340, 780],
      [1010, 760], [1190, 820], [1270, 650], [970, 665], [370, 790],
      [700, 820], [70, 820], [1350, 80]
    ];
    for (const [x, y] of trees) this.tree(x, y);

    const plaza = this.add.graphics();
    plaza.fillStyle(0x8a795d, 1);
    plaza.fillCircle(690, 427, 38);
    plaza.fillStyle(0xd9c69d, 1);
    plaza.fillCircle(690, 427, 29);
    this.add.text(653, 472, "PRAÇA CENTRAL", {
      fontFamily: "monospace",
      fontSize: "11px",
      color: "#f2e7c9"
    }).setDepth(2);
  }

  private building(
    x: number,
    y: number,
    width: number,
    height: number,
    label: string,
    wall: number,
    roof: number
  ) {
    const art = this.add.graphics();
    art.fillStyle(0x1d2a21, 0.5);
    art.fillRect(x - 5, y + 12, width + 10, height + 8);
    art.fillStyle(wall, 1);
    art.fillRect(x, y + 20, width, height);
    art.fillStyle(roof, 1);
    art.fillRect(x - 12, y, width + 24, 28);
    art.fillStyle(0x4b372a, 1);
    art.fillRect(x + width / 2 - 13, y + height - 42, 26, 42);
    art.fillStyle(0x77909a, 1);
    art.fillRect(x + 20, y + 45, 27, 25);
    art.fillRect(x + width - 47, y + 45, 27, 25);
    this.add.text(x + 7, y + height + 25, label, {
      fontFamily: "monospace",
      fontSize: "10px",
      color: "#f2e7c9",
      backgroundColor: "#17251dcc",
      padding: { x: 3, y: 2 }
    }).setDepth(2);
  }

  private tree(x: number, y: number) {
    const art = this.add.graphics();
    art.fillStyle(0x513d2d, 1);
    art.fillRect(x - 4, y + 8, 8, 20);
    art.fillStyle(0x244b32, 1);
    art.fillCircle(x, y, 19);
    art.fillStyle(0x386a43, 1);
    art.fillCircle(x - 6, y - 5, 12);
    art.fillStyle(0x4b8150, 1);
    art.fillCircle(x + 7, y - 3, 10);
  }

  private renderPeople() {
    const activeIds = new Set(this.citizens.map((citizen) => citizen.id));
    for (const [id, sprite] of this.sprites) {
      if (!activeIds.has(id)) {
        sprite.destroy();
        this.sprites.delete(id);
        this.characterSprites.delete(id);
      }
    }

    for (const citizen of this.citizens) {
      let container = this.sprites.get(citizen.id);
      if (!container) {
        const shadow = this.add.ellipse(0, 8, 15, 6, 0x17221b, 0.65);
        const frameBase = ((citizen.id - 1) % 21) * 12;
        const character = this.add.sprite(0, -2, "citizens", frameBase + 1)
          .setOrigin(0.5, 0.5)
          .setScale(1.45);
        const label = this.add.text(
          0,
          16,
          citizen.is_player ? "VOCÊ" : citizen.name.split(" ")[0],
          {
            fontFamily: "monospace",
            fontSize: "9px",
            color: "#ffffff",
            backgroundColor: "#17231dcc",
            padding: { x: 2, y: 1 }
          }
        ).setOrigin(0.5, 0);
        container = this.add.container(citizen.x * 32, citizen.y * 32, [shadow, character, label]);
        container.setDepth(citizen.y * 32 + 5);
        this.sprites.set(citizen.id, container);
        this.characterSprites.set(citizen.id, character);
      } else {
        container.setPosition(citizen.x * 32, citizen.y * 32);
        container.setDepth(citizen.y * 32 + 5);
      }
    }
  }

  update(_time: number, delta: number) {
    const player = this.citizens.find((citizen) => citizen.is_player);
    if (!player) return;

    let dx = 0;
    let dy = 0;
    if (this.cursors.left.isDown || this.keys.A.isDown) dx -= 1;
    if (this.cursors.right.isDown || this.keys.D.isDown) dx += 1;
    if (this.cursors.up.isDown || this.keys.W.isDown) dy -= 1;
    if (this.cursors.down.isDown || this.keys.S.isDown) dy += 1;

    const length = Math.hypot(dx, dy);
    const character = this.characterSprites.get(player.id);
    const frameBase = ((player.id - 1) % 21) * 12;
    if (length === 0) {
      character?.setFrame(frameBase + this.facing * 3 + 1);
      return;
    }

    if (Math.abs(dx) > Math.abs(dy)) this.facing = dx < 0 ? 1 : 2;
    else this.facing = dy < 0 ? 3 : 0;
    this.walkClock += delta;
    if (this.walkClock >= 150) {
      this.walkClock = 0;
      this.walkFrame = (this.walkFrame + 1) % 3;
    }
    character?.setFrame(frameBase + this.facing * 3 + this.walkFrame);

    const speed = 165 / 32;
    const step = speed * (delta / 1000) / length;
    player.x = Math.max(1.5, Math.min(42, player.x + dx * step));
    player.y = Math.max(1.5, Math.min(27, player.y + dy * step));

    const sprite = this.sprites.get(player.id);
    if (sprite) {
      sprite.setPosition(player.x * 32, player.y * 32);
      sprite.setDepth(player.y * 32 + 5);
    }

    this.saveClock += delta;
    if (this.saveClock >= 400) {
      this.saveClock = 0;
      this.onMove(player.x, player.y);
    }
  }
}
