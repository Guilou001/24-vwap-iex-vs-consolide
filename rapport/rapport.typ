#set document(title: "Le flux gratuit voit 1,4 % du marché : ce qu'il fait dire à un signal", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [vwap-iex-vs-consolide], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Le flux gratuit voit 1,4 % du marché : ce qu'il fait dire à un signal]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-31 · #link("https://github.com/Guilou001")[Guilou001]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Toute réplication à budget nul calcule le prix moyen pondéré par les volumes sur le flux d'IEX, la seule bourse américaine qui publie ses transactions sans abonnement. Les pupitres, eux, se réfèrent au flux consolidé, qui les voit toutes. Ce dépôt mesure de combien les deux moyennes s'écartent, puis rejoue le signal du dépôt 21 sur chacune.

*Résultat en une phrase.* IEX est présent à *91,9 %* des minutes de séance sur QQQ, donc les trous ne sont pas le problème ; mais avec *1,4 %* du volume, sa moyenne pondérée s'écarte de la vraie de *9,6 cents en médiane*, ce qui fait diverger la position tenue *une minute sur vingt-neuf* et change le rendement du signal de *+339 % à +189 %* sur QQQ. Le même exercice sur SPY donne *+75 % contre +105 %*, soit l'écart en sens inverse : ce n'est pas un biais qu'on corrige, c'est du bruit qui flatte aussi souvent qu'il pénalise.

_Summary in English. Every zero-budget replication computes VWAP on the IEX feed, the only US venue publishing trades for free. Over 1 514 sessions from August 2020 to August 2026, IEX carries 1.4 % of consolidated volume on QQQ but prints a bar in 91.9 % of session minutes, so sparsity is not the issue. Its running VWAP nevertheless sits a median 9.6 cents away from the consolidated one, exceeds one cent on 93.8 % of minutes, and exceeds the price-to-VWAP distance the signal actually measures on 5.3 % of minutes. Replaying the VWAP day-trading rule of repository 21 on each feed: 339 % versus 189 % total return on QQQ, but 75 % versus 105 % on SPY. The two feeds hold opposite positions on 3.4 % of minutes. A four-way decomposition attributes more of the damage to the VWAP than to the price. Polygon, an independent aggregator, reprices the consolidated feed identically to a hundredth of a cent, which rules out the provider as the source of the gap._

== 1. La question posée

*Les deux flux, en mots simples.* Une action américaine ne s'échange pas à un seul endroit. Une transaction peut se faire sur seize bourses et sur une trentaine de systèmes privés, et toutes remontent à un agrégateur officiel, le *flux consolidé*, qui est ce que voient les pupitres. IEX est une de ces bourses, et c'est celle que les fournisseurs de données offrent sans abonnement.

*Pourquoi cela devrait être sans conséquence, et pourquoi ce ne l'est pas.* Le prix instantané est le même partout, à l'arbitrage près : une action ne peut pas valoir 400,10 dollars sur une bourse et 400,50 sur la voisine. Mais le prix moyen pondéré par les volumes n'est pas un prix, c'est une *moyenne sur les transactions vues*. Le consolidé les voit toutes, IEX en voit une sur soixante-treize, et rien ne garantit que la moyenne d'un soixante-dixième ressemble à la moyenne du tout.

*La question du dépôt.* De combien les deux moyennes s'écartent, et cet écart suffit-il à faire changer d'avis un signal qui compare le prix à la moyenne ?

== 2. D'où vient le projet, et ce qu'il apporte

Quatre apports.

- *Deux mesures de couverture qui ne disent pas la même chose* : la part du volume, qui donne le

poids de la bourse, et la part des minutes, qui donne la densité de l'information reçue.

- *La distribution complète de l'écart* entre les deux moyennes, sur 590 000 minutes et deux

symboles, avec le point de comparaison qui la rend interprétable.

- *Le signal du dépôt 21 rejoué en quatre versions*, qui séparent l'erreur venue du prix de celle

venue de la moyenne.

- *Un contrôle par un troisième fournisseur*, sans quoi la comparaison entre deux séries du même

fournisseur ne prouverait rien.

*Deux corrections à des mesures antérieures de ce portefeuille*, qui vont dans le même sens. La première annonçait qu'IEX ne voit rien sur 57 % des minutes ; c'est vrai de la *journée entière*, extensions d'avant et d'après-bourse comprises, et faux de la séance, où la présence atteint 99,7 % en juin 2026. La seconde annonçait 3,45 % d'écart de volume entre deux agrégateurs du consolidé ; c'est encore la journée entière, et la séance seule donne *0,66 %*. La règle qui s'en dégage vaut au-delà de ce dépôt : une statistique calculée sur les 1 440 minutes du jour décrit surtout les heures creuses, alors qu'une stratégie de séance ne vit que dans 390 d'entre elles.

== 3. Les données

Barres d'une minute d'Alpaca, prix bruts, sur QQQ et SPY, du *3 août 2020 au 28 août 2026*, sur les deux flux. Séances régulières de 9 h 30 à 16 h, séances écourtées de veille de congé retirées : *1 514 séances* sur QQQ et 1 512 sur SPY, soit 590 460 et 589 680 minutes.

La fenêtre commence au 3 août 2020 parce que c'est là que commence la profondeur d'Alpaca sur le flux IEX, mesurée le 30 août 2026. Cette profondeur est glissante, donc elle avance : une réexécution plus tard ne retrouvera pas les premiers mois.

Contrôle indépendant : Polygon, sur juin 2026, la limite de son offre gratuite étant de deux ans glissants.

== 4. Les résultats

=== 4.1 Le problème n'est pas qu'IEX se taise

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*QQQ*],
    [*SPY*],
    [Part du volume consolidé],
    [*1,37 %*],
    [1,95 %],
    [Part des minutes avec au moins une transaction],
    [*91,9 %*],
    [98,2 %],
    [Minutes muettes],
    [48 053],
    [10 743],
    [Retard médian à la première transaction du jour],
    [0 minute],
    [0 minute],
    [Retard le plus long jamais observé],
    [1 minute],
    [0 minute],
)

Comment lire ce tableau, en trois constats. Le premier est que les deux mesures racontent des histoires opposées : IEX porte moins de 2 % du volume et publie pourtant une barre dans plus de neuf minutes sur dix, donc il est presque toujours là mais ne voit presque rien. Le deuxième est que le retard à l'ouverture est nul en médiane et n'atteint jamais deux minutes, donc un programme branché sur ce flux n'attend pas pour prendre position. Le troisième est que la présence s'améliore avec le temps, de 83,5 % en 2021 à 99,4 % sur les huit premiers mois de 2026 sur QQQ : le trou se referme, et pourtant le reste de ce dépôt montre que le problème demeure.

#figure(image("../results/figures/couverture.png", width: 100%), caption: [La part du volume et la part des minutes, année par année])

Comment lire cette figure : deux volets, parce que les deux grandeurs n'ont ni la même échelle ni le même sens et que les superposer suggérerait une relation que rien n'établit. Les années 2020 et 2026 sont partielles, 104 et 165 séances contre 250 pour les autres.

=== 4.2 L'écart entre les deux moyennes, et ce à quoi il faut le comparer

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*QQQ*],
    [*SPY*],
    [Écart médian, en valeur absolue],
    [*9,61 cents*],
    [6,25 cents],
    [Biais moyen, signé],
    [+1,91 cent],
    [+0,90 cent],
    [Écart type],
    [22,93 cents],
    [16,49 cents],
    [Part des minutes au-delà d'un cent],
    [*93,8 %*],
    [90,0 %],
    [Part des minutes au-delà de cinq cents],
    [71,1 %],
    [57,5 %],
)

Comment lire ce tableau, en trois constats. Le premier est que l'écart dépasse le cent, c'est-à-dire le pas de cotation, sur plus de neuf minutes sur dix : les deux moyennes ne sont pas la même grandeur mesurée deux fois, ce sont deux grandeurs différentes. Le deuxième est que le biais est positif dans les deux cas, donc la moyenne d'IEX se tient au-dessus de celle du marché, ce que ce dépôt mesure sans l'expliquer. Le troisième est que ces cents ne veulent rien dire tant qu'on ne les compare à rien, et c'est l'objet du tableau suivant.

Le point de comparaison est la *distance entre le prix et sa moyenne pondérée*, puisque c'est le signe de cette distance que la règle regarde.

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*QQQ*],
    [*SPY*],
    [Distance médiane entre le prix et sa moyenne],
    [23,3 points de base],
    [15,6 points de base],
    [Écart médian entre les deux moyennes],
    [2,35 points de base],
    [1,27 point de base],
    [Rapport des deux],
    [*10,1 %*],
    [8,2 %],
    [Part des minutes où l'écart dépasse la distance],
    [*5,3 %*],
    [4,5 %],
)

Comment lire ce tableau, en trois constats. Le premier est que l'écart vaut un dixième de ce que le signal mesure : dans le cas ordinaire, il ne fait pas basculer la décision. Le deuxième est que la dernière ligne dit ce qui compte vraiment, à savoir qu'une minute sur dix-neuf voit un écart plus grand que la distance elle-même, donc suffisant pour renverser le signe à lui seul. Le troisième est que ces 5,3 % ne sont pas une petite quantité pour une stratégie qui prend 390 décisions par jour : c'est une vingtaine de minutes par séance où le flux gratuit décide autre chose.

#figure(image("../results/figures/distribution.png", width: 100%), caption: [La densité de l'écart entre les deux moyennes])

Comment lire cette figure : l'axe est coupé à cinquante cents de part et d'autre, la queue au-delà étant trop fine pour se voir. La part des minutes hors cadre est écrite dans le titre.

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Quantile de l'écart absolu*],
    [*QQQ, en cents*],
    [*QQQ, en points de base*],
    [*SPY, en cents*],
    [médiane],
    [9,61],
    [2,35],
    [6,25],
    [trois quarts],
    [19,05],
    [4,76],
    [12,86],
    [neuf dixièmes],
    [33,44],
    [8,58],
    [23,14],
    [dix-neuf vingtièmes],
    [45,77],
    [11,88],
    [33,18],
    [quatre-vingt-dix-neuf centièmes],
    [79,32],
    [21,15],
    [59,06],
    [*maximum*],
    [*603,95*],
    [*145,68*],
    [395,47],
)

Comment lire ce tableau, en trois constats. Le premier est que la queue est longue : le centième le plus défavorable dépasse 79 cents sur QQQ, et le pire atteint 6 dollars. Le deuxième est que ce pire cas vaut 145 points de base, donc six fois la distance médiane entre le prix et sa moyenne : ces minutes-là, le signal calculé sur IEX ne mesure plus rien. Le troisième est que SPY est partout meilleur que QQQ, dans le même rapport que la part de volume, ce qui est le signe attendu si l'écart vient bien de la taille de l'échantillon.

#figure(image("../results/figures/moments.png", width: 100%), caption: [L'écart moyen selon le moment de la séance])

Comment lire cette figure : l'écart croît de façon monotone du matin au soir, de 2,59 à 4,52 points de base sur QQQ. C'est ce qu'on attend d'une moyenne cumulée, dont les deux versions divergent en s'accumulant, et c'est le pire moment possible : la dernière demi-heure est celle où un signal de suivi de tendance décide de solder.

=== 4.3 Le même signal, joué sur chacun des deux flux

Le signal est celui du dépôt 21 : acheter quand le prix est au-dessus de sa moyenne pondérée depuis l'ouverture, vendre à découvert sinon, solder à la clôture. Le rendement encaissé est toujours celui du vrai marché, quel que soit le flux qui décide.

#table(
  columns: 7,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Symbole*],
    [*Version*],
    [*Rendement total*],
    [*Par an*],
    [*Sharpe*],
    [*Pire creux*],
    [*Changements par jour*],
    [QQQ],
    [tout consolidé],
    [*+339,5 %*],
    [27,9 %],
    [*1,61*],
    [17,2 %],
    [16,20],
    [QQQ],
    [tout IEX],
    [*+189,2 %*],
    [19,3 %],
    [*1,12*],
    [22,9 %],
    [16,71],
    [SPY],
    [tout consolidé],
    [*+75,1 %*],
    [9,8 %],
    [*0,75*],
    [19,5 %],
    [17,20],
    [SPY],
    [tout IEX],
    [*+105,0 %*],
    [12,7 %],
    [*0,98*],
    [13,8 %],
    [17,55],
)

Comment lire ce tableau, en trois constats. Le premier est que le flux gratuit coûte 150 points de rendement sur QQQ et en *rapporte 30 sur SPY* : l'erreur n'a pas de signe, donc elle ne se corrige pas, et un chercheur qui aurait choisi SPY conclurait que le flux gratuit convient très bien. Le deuxième est que le flux gratuit fait tourner davantage, 16,71 changements de position par jour contre 16,20, donc il coûte aussi plus cher à exécuter, et cet effet-là, lui, va toujours dans le même sens. Le troisième est qu'à un cent de glissement le classement se durcit : la version consolidée de QQQ garde +25,9 % quand la version IEX tombe à *−20,8 %*.

#figure(image("../results/figures/versions.png", width: 100%), caption: [Le ratio de Sharpe des quatre versions])

Comment lire cette figure : les deux barres du milieu croisent les flux, prix de l'un et moyenne de l'autre. Sur QQQ elles se rangent entre les deux versions pures, et celle qui garde la moyenne consolidée est la meilleure des deux, donc la moyenne porte plus d'erreur que le prix. Sur SPY l'ordre n'est même pas respecté, la version au prix consolidé et à la moyenne IEX dépassant les deux autres : c'est la signature d'un bruit et non celle d'un défaut systématique.

=== 4.4 Une minute sur vingt-neuf, les deux flux tiennent des positions opposées

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*QQQ*],
    [*SPY*],
    [Même position],
    [96,26 %],
    [96,94 %],
    [*Positions opposées*],
    [*3,42 %*],
    [*2,74 %*],
    [IEX n'a encore rien vu, donc ne décide rien],
    [0,067 %],
    [0,066 %],
)

Comment lire ce tableau, en trois constats. Le premier est que le silence est cinquante fois plus rare que le contresens : le trou de couverture, qui est le défaut visible du flux gratuit, n'est pas celui qui coûte. Le deuxième est que les positions opposées touchent une minute sur vingt-neuf sur QQQ, et qu'une position opposée ne coûte pas le mouvement du marché mais deux fois ce mouvement. Le troisième est que ces 3,42 % suffisent à expliquer l'écart de rendement de la section précédente, alors que le silence, à 0,067 %, ne pourrait rien expliquer du tout.

#figure(image("../results/figures/desaccords.png", width: 100%), caption: [Ce qui sépare les deux versions du signal])

Comment lire cette figure : l'échelle est logarithmique, sans quoi les deux petites barres seraient invisibles à côté de l'accord à 96 %.

=== 4.5 Le contrôle : ce n'est pas le fournisseur

Tout ce qui précède compare deux séries livrées par le même fournisseur. Si ce fournisseur se trompait sur l'une des deux, rien dans la comparaison ne le montrerait.

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Contrôle sur QQQ, juin 2026*],
    [*Mesure*],
    [Minutes de séance communes aux deux agrégateurs],
    [8 190],
    [Minutes publiées par Alpaca et absentes de Polygon],
    [*0*],
    [Prix identiques au dixième de cent],
    [*100 %*],
    [Écart de prix maximal],
    [0,01 cent],
    [Écart de volume moyen],
    [0,66 %],
)

Comment lire ce tableau, en trois constats. Le premier est que deux chaînes de collecte indépendantes publient exactement les mêmes prix, à un centième de cent près sur les 8 190 minutes du mois : le flux consolidé de ce dépôt est bien le flux consolidé. Le deuxième est que l'écart de volume de 0,66 % subsiste, et qu'une étude de volume, contrairement à une étude de prix, ne peut donc pas prendre l'un ou l'autre indifféremment. Le troisième est ce que ce contrôle *ne* prouve pas : il n'exclut pas que les deux agrégateurs se trompent de la même façon, et le dépôt ne le prétend pas.

== 5. La méthode, pas à pas

+ *Poser les deux flux sur la même grille de minutes*, celle du consolidé, parce qu'elle est complète. Les minutes où IEX n'a rien vu restent vides.
+ *Ne rien inventer à leur place.* Une minute sans transaction chez IEX n'ajoute rien aux deux cumuls, donc laisse sa moyenne pondérée inchangée ; le prix, lui, est reporté depuis la dernière minute vue, ce qui est le dernier prix qu'un programme branché sur ce seul flux connaîtrait.
+ *Cumuler séparément* le montant échangé et le volume, de l'ouverture à chaque minute, sur chacun des deux flux.
+ *Rejouer le signal en quatre versions*, le prix et la moyenne venant chacun de l'un ou l'autre flux, la position d'une minute étant toujours décidée par la minute précédente.
+ *Confronter le consolidé à un troisième fournisseur* sur la fenêtre que son offre gratuite permet.

== 6. Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest                        # 19 tests fermés, sans réseau ni données de marché\nuv run vic fetch --controle          # les deux flux sur six ans, plus le mois de contrôle\nuv run vic tout                      # les cinq études et les cinq figures", block: true, lang: "bash")

Le téléchargement demande une clé Alpaca, et le contrôle une clé Polygon, à poser dans l'environnement ou dans un fichier local que le client partagé lit. Aucune clé n'est dans le dépôt. Les tests tournent sur deux séances de quatre minutes dont chaque réponse se calcule de tête. Tous les chiffres de ce README viennent des fichiers de #raw("results/tables/").

== 7. Limites, avec leur statut

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Limite*],
    [*Statut*],
    [La fenêtre commence en août 2020, faute de profondeur sur le flux IEX],
    [mesuré ; la profondeur est glissante, donc une réexécution ultérieure aura une fenêtre plus courte],
    [Deux symboles seulement, tous deux très liquides],
    [déclaré ; sur un titre peu traité, la part des minutes muettes serait bien plus haute, donc les écarts mesurés ici sont un plancher],
    [Le biais positif de la moyenne IEX n'est pas expliqué],
    [déclaré ; il est mesuré à +1,91 cent sur QQQ et +0,90 sur SPY, et sa cause n'est pas établie],
    [Le contrôle Polygon ne porte que sur un mois],
    [déclaré ; c'est la limite de l'offre gratuite, et un mois suffit à trancher entre accord et désaccord, pas à mesurer une dérive lente],
    [Le contrôle n'exclut pas une erreur commune aux deux agrégateurs],
    [reconnu ; il établit l'accord, pas la vérité],
    [Le report du dernier prix connu est un choix],
    [déclaré ; c'est ce que fait un programme branché sur le seul flux IEX, et une autre convention donnerait d'autres nombres],
    [Les rendements sont calculés de clôture de minute à clôture de minute],
    [déclaré ; le glissement facturé approche le coût réel d'exécution sans le modéliser],
    [L'écart de rendement entre les deux flux n'est pas encadré par une incertitude],
    [déclaré ; deux symboles ne permettent pas d'en estimer une, et c'est précisément pourquoi le résultat est présenté comme du bruit et non comme un biais],
)

== 8. Crédits, licence, citation

Données de marché : Alpaca, flux consolidé et flux IEX, compte gratuit, usage personnel ; Polygon, offre gratuite, pour le seul contrôle. Aucune barre n'est redistribuée. Code sous licence MIT, rapport sous licence CC BY 4.0. Figures et client de données produits par #link("https://github.com/Guilou001/gv-fintools")[gv-fintools].

Voisinage dans le portefeuille : #link("https://github.com/Guilou001/21-vwap-intrajournalier")[21-vwap-intrajournalier] porte le signal rejoué ici et mesure ce que le glissement lui coûte. Celui-ci ne touche pas au signal et mesure ce que la source de données lui fait dire. #link("https://github.com/Guilou001/22-derniere-demi-heure")[22-derniere-demi-heure] travaille sur le même flux consolidé et sur la même fenêtre. Le rapport #raw("rapport/rapport.pdf") est engendré depuis ce README.
