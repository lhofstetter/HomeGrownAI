import Svg, {
  Circle,
  Defs,
  G,
  LinearGradient,
  Path,
  Stop,
  type SvgProps,
} from 'react-native-svg';

type HomeGrownAIIconProps = SvgProps & {
  size?: number;
};

export function HomeGrownAIIcon({
  size = 128,
  ...props
}: HomeGrownAIIconProps) {
  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 1024 1024"
      fill="none"
      {...props}
    >
      <Defs>
        {/* House */}
        <LinearGradient
          id="hgai-house"
          x1={260}
          y1={180}
          x2={760}
          y2={900}
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset={0} stopColor="#107C70" />
          <Stop offset={0.5} stopColor="#075B58" />
          <Stop offset={1} stopColor="#023F42" />
        </LinearGradient>

        {/* Large leaf */}
        <LinearGradient
          id="hgai-leaf-left"
          x1={225}
          y1={335}
          x2={500}
          y2={620}
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset={0} stopColor="#A8F21D" />
          <Stop offset={0.42} stopColor="#51D339" />
          <Stop offset={1} stopColor="#008B69" />
        </LinearGradient>

        {/* Small leaf */}
        <LinearGradient
          id="hgai-leaf-right"
          x1={760}
          y1={445}
          x2={540}
          y2={640}
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset={0} stopColor="#9EF01A" />
          <Stop offset={0.48} stopColor="#45CF3B" />
          <Stop offset={1} stopColor="#008B69" />
        </LinearGradient>

        {/* Plant/circuit traces */}
        <LinearGradient
          id="hgai-circuit"
          x1={470}
          y1={570}
          x2={520}
          y2={910}
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset={0} stopColor="#FFFFFF" />
          <Stop offset={0.55} stopColor="#E8FFD7" />
          <Stop offset={1} stopColor="#A5F56B" />
        </LinearGradient>

        {/* Circuit nodes */}
        <LinearGradient
          id="hgai-node"
          x1={300}
          y1={700}
          x2={690}
          y2={900}
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset={0} stopColor="#63DE2A" />
          <Stop offset={1} stopColor="#009B70" />
        </LinearGradient>

        {/* Leaf highlight */}
        <LinearGradient
          id="hgai-highlight"
          x1={270}
          y1={370}
          x2={500}
          y2={600}
          gradientUnits="userSpaceOnUse"
        >
          <Stop offset={0} stopColor="#C7FF36" stopOpacity={0.72} />
          <Stop offset={1} stopColor="#65E937" stopOpacity={0} />
        </LinearGradient>
      </Defs>

      {/* House */}
      <Path
        d="
          M 142 458
          C 124 474 117 499 125 523
          C 135 553 161 572 193 572

          L 216 572
          L 216 819

          C 216 868 256 908 305 908
          L 719 908

          C 768 908 808 868 808 819
          L 808 572
          L 831 572

          C 863 572 889 553 899 523
          C 907 499 900 474 882 458

          L 797 383
          L 797 221

          C 797 196 777 176 752 176
          L 700 176

          C 675 176 655 196 655 221
          L 655 258

          L 545 162

          C 526 145 498 145 479 162
          L 142 458

          Z
        "
        fill="url(#hgai-house)"
      />

      {/* Large left leaf */}
      <Path
        d="
          M 508 632
          C 482 539 432 451 352 397
          C 300 362 244 344 194 334

          C 190 415 211 486 259 536
          C 307 586 369 602 424 602

          C 454 602 482 612 508 632
          Z
        "
        fill="url(#hgai-leaf-left)"
        stroke="url(#hgai-circuit)"
        strokeWidth={24}
        strokeLinejoin="round"
      />

      {/* Soft highlight inside large leaf */}
      <Path
        d="
          M 218 350
          C 291 372 365 407 422 462
          C 457 496 483 534 502 574

          C 457 529 402 489 340 456
          C 293 431 250 398 218 350
          Z
        "
        fill="url(#hgai-highlight)"
      />

      {/* Right leaf */}
      <Path
        d="
          M 525 641
          C 553 559 613 488 687 456
          C 721 441 756 434 789 434

          C 788 502 763 558 719 596
          C 678 631 629 641 587 637

          C 565 635 545 636 525 641
          Z
        "
        fill="url(#hgai-leaf-right)"
        stroke="url(#hgai-circuit)"
        strokeWidth={24}
        strokeLinejoin="round"
      />

      {/* Soft highlight inside small leaf */}
      <Path
        d="
          M 758 456
          C 704 474 654 503 615 541
          C 583 572 557 605 537 629

          C 583 594 625 570 668 548
          C 710 527 740 496 758 456
          Z
        "
        fill="url(#hgai-highlight)"
        opacity={0.68}
      />

      {/* Plant stem + circuit traces */}
      <G
        fill="none"
        stroke="url(#hgai-circuit)"
        strokeWidth={28}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* Main stem */}
        <Path
          d="
            M 512 595
            L 512 826
          "
        />

        {/* Left circuit branch */}
        <Path
          d="
            M 512 678
            C 490 724 445 769 390 814
            C 374 827 354 816 354 795
            L 354 748
          "
        />

        {/* Right circuit branch */}
        <Path
          d="
            M 512 678
            C 534 724 579 769 634 814
            C 650 827 670 816 670 795
            L 670 748
          "
        />
      </G>

      {/* Left node */}
      <Circle
        cx={354}
        cy={715}
        r={53}
        fill="#F3FFE9"
      />
      <Circle
        cx={354}
        cy={715}
        r={32}
        fill="url(#hgai-node)"
      />

      {/* Right node */}
      <Circle
        cx={670}
        cy={715}
        r={53}
        fill="#F3FFE9"
      />
      <Circle
        cx={670}
        cy={715}
        r={32}
        fill="url(#hgai-node)"
      />

      {/* Bottom node */}
      <Circle
        cx={512}
        cy={862}
        r={56}
        fill="#DFFFF0"
      />
      <Circle
        cx={512}
        cy={862}
        r={33}
        fill="url(#hgai-node)"
      />
    </Svg>
  );
}

export default HomeGrownAIIcon;
