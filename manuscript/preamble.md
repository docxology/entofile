# LaTeX Preamble

```latex
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}
\hypersetup{colorlinks=true,allcolors=red}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}
\usepackage{tikz}
\usepackage{etoolbox}
\usepackage{eso-pic}

\definecolor{EntoInk}{HTML}{172126}
\definecolor{EntoCoverPaper}{HTML}{F7F8F5}
\definecolor{EntoGraphite}{HTML}{1D252A}
\definecolor{EntoSignal}{HTML}{A51E2D}
\definecolor{EntoRule}{HTML}{6B7378}

\AtBeginEnvironment{titlepage}{%
  \thispagestyle{empty}\color{EntoInk}%
  \AddToShipoutPictureBG*{%
  \begin{tikzpicture}[remember picture,overlay]
    \fill[EntoCoverPaper] (current page.south west) rectangle (current page.north east);
    \fill[EntoGraphite] (current page.north west) rectangle ([yshift=-1.75cm]current page.north east);
    \fill[EntoSignal] ([yshift=-1.75cm]current page.north west) rectangle ([yshift=-1.87cm]current page.north east);
    \node[anchor=north west, text=white, font=\sffamily\bfseries\small]
      at ([xshift=0.55in,yshift=-0.47in]current page.north west) {ENTO 0.5.0};
    \node[anchor=north east, text=white, font=\sffamily\small]
      at ([xshift=-0.55in,yshift=-0.47in]current page.north east) {stable default wire format 0.5.0};
    \draw[EntoRule,line width=0.55pt]
      ([xshift=0.50in,yshift=-0.50in]current page.north west)
      rectangle
      ([xshift=-0.50in,yshift=0.50in]current page.south east);
  \end{tikzpicture}%
  }%
}
\AtEndEnvironment{titlepage}{\color{black}}
```
