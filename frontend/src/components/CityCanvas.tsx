import { useEffect, useRef } from "react";
import Phaser from "phaser";
import { CityScene } from "../game/CityScene";
import type { Citizen } from "../game/CityScene";

export default function CityCanvas({
  citizens,
  onSelect,
  onMove
}: {
  citizens: Citizen[];
  onSelect: (citizen: Citizen) => void;
  onMove: (x: number, y: number) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const game = useRef<Phaser.Game | null>(null);

  useEffect(() => {
    if (!host.current) return;
    const scene = new CityScene(onSelect, onMove);
    game.current = new Phaser.Game({
      type: Phaser.CANVAS,
      parent: host.current,
      width: 960,
      height: 560,
      backgroundColor: "#263d30",
      pixelArt: true,
      roundPixels: true,
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
      },
      scene
    });
    return () => {
      game.current?.destroy(true);
      game.current = null;
    };
  }, [onSelect, onMove]);

  useEffect(() => {
    const scene = game.current?.scene.getScene("CityScene") as CityScene | undefined;
    scene?.setCitizens(citizens);
  }, [citizens]);

  return <div className="city-canvas" ref={host} aria-label="Mapa explorável da Cidade Viva" />;
}
