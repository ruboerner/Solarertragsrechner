import marimo

__generated_with = "0.6.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo

    mo.Html(
            """
        <link href="https://fonts.googleapis.com/css?family=Atkinson+Hyperlegible" rel="stylesheet">

        <style>
            :root {
                --text-font:    "Atkinson Hyperlegible";
                --heading-font: "Atkinson Hyperlegible";
            }
        </style>
        """
    )
    return mo,


@app.cell
def __():
    import pysolar.solar as so
    # from zoneinfo import ZoneInfo
    import pytz
    from datetime import datetime, timedelta
    import time
    import os
    import math
    import numpy as np
    from matplotlib import pyplot as plt, dates
    from scipy import integrate
    import scienceplots
    plt.style.use(['science', 'notebook'])
    return (
        dates,
        datetime,
        integrate,
        math,
        np,
        os,
        plt,
        pytz,
        scienceplots,
        so,
        time,
        timedelta,
    )


@app.cell
def __(datetime, math, np, pytz, so, timedelta):
    def daterange(start_date, end_date):
        delta = timedelta(minutes=5)
        while start_date < end_date:
            yield start_date
            start_date += delta

    def getcos(azimuth, elevation, orientation, angle):
        return np.array([
            np.dot(get_n(a, e), get_n(orientation, angle)) for a, e in zip(azimuth, elevation)
        ])

    def get_attenuation(when, altitude_deg):
        import pysolar
        # from Masters, p. 412
        is_daytime = (altitude_deg > 0)
        day = pysolar.radiation.math.tm_yday(when)
        flux = pysolar.radiation.get_apparent_extraterrestrial_flux(day)
        optical_depth = pysolar.radiation.get_optical_depth(day)
        # air_mass_ratio = pysolar.radiation.get_air_mass_ratio(altitude_deg)
        sin_beta = math.sin(math.radians(altitude_deg))
        air_mass_ratio = np.sqrt((708 * sin_beta)**2 + 1417) - 708 * sin_beta
        return pysolar.radiation.math.exp(-1 * optical_depth * air_mass_ratio) * is_daytime

    def get_n(el, az):
        return np.array([
            np.cos(np.deg2rad(az)) * np.cos(np.deg2rad(el)),
            np.cos(np.deg2rad(az)) * np.sin(np.deg2rad(el)),
            np.sin(np.deg2rad(az))
        ])

    def panel(year, month, day, orientation, angle, begin=4, end=22, lat=50.906923, lon=13.333424):
        timezone = pytz.timezone('Europe/Berlin')
        start_date_ = datetime(year, month, day, begin, 0)
        end_date_ = datetime(year, month, day, end, 0)
        start_date = timezone.localize(start_date_)
        end_date = timezone.localize(end_date_)
        azimuth = []
        elevation = []
        hours = []
        for d in daterange(start_date, end_date):
            hours.append(d)
            azimuth.append(so.get_azimuth(lat, lon, d))
            elevation.append(so.get_altitude(lat, lon, d))

        attn = np.array([get_attenuation(start_date, alt) for alt in elevation])

        cosgamma = np.hstack(getcos(azimuth, elevation, orientation, angle))
        cosgamma = np.clip(cosgamma, 0, 1)
        remove = np.where(np.array(elevation) < 0, True, False)
        cosgamma[remove] = 0.0
        return cosgamma, attn, hours, elevation
    return daterange, get_attenuation, get_n, getcos, panel


@app.cell
def __(np):
    def get_index_sunrise_sunset(elevation):
        el = np.array(elevation)
        first = next(x for x, val in enumerate(el) if val > 0)
        last =  next(x for x in range(np.size(el)-1, -1, -1) if el[x] > 0)
        return first, last
    return get_index_sunrise_sunset,


@app.cell
def __(mo):
    mo.md(
        """
        # Optimale Ausrichtung von Solarpanels

        Diese Anwendung berechnet die von bis zu vier Solarmodulen erzeugte Leistung. 
        Benutzer können das gewünschte Datum sowie die Azimut- und Anstellwinkel der Module eingeben. 
        Die Web-Anwendung basiert auf der genauen Berechnung des Sonnenstandes, die vom Python-Modul [pysolar](https://github.com/pingswept/pysolar) bereitgestellt wird. 

        Darüberhinaus werden die von den Solarmodulen über einen Tag umgewandelte Energie in kWh sowie die Volllaststunden angezeigt.

        Durch Bewertung des erzielten Gesamtertrages ist es möglich, die optimale Ausrichtung der Solarmodule *interaktiv* zu ermitteln und die Energieausbeute zu maximieren. 


        """
    ).callout(kind="info")
    return


@app.cell
def __(mo):
    hintergrund = mo.md(
        r'''
    ## Warum der Sonnenstand für die Berechnung der optimalen Ausrichtung eines Solarpanels wichtig ist

    Um die maximale Effizienz eines Solarpanels zu gewährleisten, muss es so ausgerichtet werden, dass es die größtmögliche Menge an Sonnenstrahlung einfängt. Dafür ist es notwendig, die Orientierung des Solarpanels zu kennen, die durch zwei Hauptparameter beschrieben wird: Azimut und Anstellwinkel.

    - **Azimut**: Dies ist der Winkel in der horizontalen Ebene, gemessen von Norden im Uhrzeigersinn. Der Azimutwinkel des Solarpanels sollte so eingestellt werden, dass es möglichst direkt auf die Sonne ausgerichtet ist, je nachdem, zu welcher Tageszeit und in welcher Jahreszeit die meiste Sonneneinstrahlung zu erwarten ist.

    - **Anstellwinkel**: Dies ist der Neigungswinkel des Solarpanels relativ zur Horizontalen. Der Anstellwinkel sollte so eingestellt werden, dass die Sonnenstrahlen im rechten Winkel auf das Panel treffen. Dies maximiert die absorbierte Sonnenenergie und verbessert die Effizienz der Stromerzeugung.

    Der Sonnenstand ändert sich im Tages- und Jahresverlauf ständig, daher ist es wichtig, diese Veränderungen zu berücksichtigen, um die optimale Ausrichtung des Solarpanels kontinuierlich zu gewährleisten. Eine genaue Berechnung und Anpassung von Azimut und Anstellwinkel basierend auf dem aktuellen Sonnenstand ermöglicht es, die Energieausbeute eines Solarpanels zu maximieren.

    ## Anleitung zur Berechnung des Skalarprodukts aus den Winkeln von Solarpanel und Sonnenstand

    Das Skalarprodukt zwischen zwei Vektoren kann verwendet werden, um den Winkel zwischen dem Solarpanel und der Sonnenstrahlung zu berechnen. Hier ist eine Schritt-für-Schritt-Anleitung, wie das Skalarprodukt aus den Winkeln von Solarpanel und Sonnenstand berechnet wird:

    ### Definition der Winkel

       - **Azimut des Solarpanels ($\alpha_P$)**: Der horizontale Winkel des Solarpanels gemessen von Norden im Uhrzeigersinn.
       - **Anstellwinkel des Solarpanels ($\gamma_P$)**: Der Neigungswinkel des Solarpanels relativ zur Horizontalen.
       - **Azimut der Sonne ($\alpha_S$)**: Der horizontale Winkel der Sonne gemessen von Norden im Uhrzeigersinn.
       - **Sonnenhöhe ($\gamma_S$)**: Der Winkel der Sonne über dem Horizont.

    ### Berechnung der Richtungsvektoren

    Der Richtungsvektor des Solarpanels kann durch seine Azimut- und Anstellwinkel wie folgt dargestellt werden:

    $$     
         \mathbf{n}_{P} = \begin{pmatrix}
         \cos(\alpha_P) \cdot \cos(\gamma_P) \\\\
         \sin(\alpha_P) \cdot \cos(\gamma_P) \\\\
         \sin(\gamma_P)
         \end{pmatrix}
    $$

    Der Richtungsvektor zur Sonne kann durch ihren Azimut- und Höhenwinkel wie folgt dargestellt werden:

    $$
    \mathbf{n}_{S} = \begin{pmatrix}
         \cos(\alpha_S) \cdot \cos(\gamma_S) \\\\
         \sin(\alpha_S) \cdot \cos(\gamma_S) \\\\
         \sin(\gamma_S)
    \end{pmatrix}
    $$

    ### Berechnung des Skalarprodukts

    Das Skalarprodukt \(\mathbf{n}_{P} \cdot \mathbf{n}_{S}\) der beiden Vektoren wird berechnet als:

    $$
    \mathbf{n}_{P} \cdot \mathbf{n}_{S} = (\cos(\alpha_P) \cdot \cos(\gamma_P)) \cdot (\cos(\alpha_S) \cdot \cos(\gamma_S)) + (\sin(\alpha_P) \cdot \cos(\gamma_P)) \cdot (\sin(\alpha_S) \cdot \cos(\gamma_S)) + (\sin(\gamma_P)) \cdot (\sin(\gamma_S))
    $$

    ### Verwendung des Skalarprodukts

    Das Skalarprodukt liefert einen Wert, der proportional zum Kosinus des Winkels zwischen den beiden Vektoren ist. Dieser Wert kann verwendet werden, um die Effizienz der Ausrichtung des Solarpanels relativ zur aktuellen Position der Sonne zu bewerten.

    Durch die Berechnung des Skalarprodukts können wir feststellen, wie gut das Solarpanel zur Sonne ausgerichtet ist. Ein größerer Wert des Skalarprodukts bedeutet eine bessere Ausrichtung und damit eine höhere Effizienz bei der Energieerzeugung.


        '''
    )
    return hintergrund,


@app.cell
def __(hintergrund, mo):
    mo.accordion(
        {"Mathematischer Hintergrund": hintergrund}
    )
    return


@app.cell
def __(mo):
    date = mo.ui.date()
    return date,


@app.cell
def __(date, mo):
    mo.hstack([mo.md("Datum: "), date], gap=1.0, justify="start")
    return


@app.cell
def __(date):
    year = date.value.year
    month = date.value.month
    day = date.value.day
    return day, month, year


@app.cell
def __(mo):
    n = mo.ui.slider(1, 4, value=1)
    return n,


@app.cell
def __(mo, n):
    mo.hstack([mo.md(f"Anzahl der installierten Panels (1...4): "), n, mo.md(f"{n.value}")], gap=2.0, justify='start')
    return


@app.cell
def __(mo, n):
    panels = mo.ui.array(mo.md("{az} {el} {power}").batch(
        az=mo.ui.slider(0, 359, 5, label="Azimut", value=((i+1) * 60) % 360, show_value=True),
        el=mo.ui.slider(0, 90, 5, label="Anstellwinkel", value=30, show_value=True),
        power=mo.ui.text(value='375', label='Leistung:')) for i in range(n.value))
    mo.vstack(panels)
    return panels,


@app.cell
def __(n, np, panels):
    P = np.array([panels[i].value['power'] for i in range(n.value)], dtype=float)
    return P,


@app.cell
def __(P, day, month, n, np, panel, panels, year):
    CC, A, hours, elevation = panel(year, month, day, panels[0]["az"].value, panels[0]["el"].value)
    L = (CC * A) * P[0]
    L = np.expand_dims(L, axis=0)
    T = L[0]

    nt = len(hours)

    if n.value > 1:
        for i in range(1, n.value):
            CC = np.vstack([CC, panel(year, month, day, panels[i]["az"].value, panels[i]["el"].value)[0]])
            L = np.vstack([L, (CC[i] * A) * P[i]])
        T = np.sum(L, axis=0)
    return A, CC, L, T, elevation, hours, i, nt


@app.cell
def __(T, hours, integrate, np):
    tt = np.array([v.timestamp() - hours[0].timestamp() for v in hours])
    I = integrate.simpson(T, x=tt, dx=np.diff(tt)[0])
    return I, tt


@app.cell
def __(
    L,
    P,
    T,
    dates,
    elevation,
    get_index_sunrise_sunset,
    hours,
    n,
    np,
    plt,
    pytz,
):
    fig, ax = plt.subplots(1, 1, figsize=(11, 4))


    first, last = get_index_sunrise_sunset(elevation)

    ax.axvspan(hours[first], hours[last], color='yellow', alpha=0.3, label=None)
    ax.axvspan(hours[0], hours[first], color='darkblue', alpha=0.5, label=None)
    ax.axvspan(hours[last], hours[-1], color='darkblue', alpha=0.5, label=None)

    [ax.plot(hours, L[i], linewidth=1, label = f"Panel {str(i+1)}") for i in range(n.value)]

    ax.plot(hours, T, linewidth=3, color='green', label='Gesamtleistung')
    ax.fill_between(hours, T, color='green', alpha=0.3)
    ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M', tz=pytz.timezone("Europe/Berlin")))
    ax.set_ylim(0, np.sum(P))
    ax.set_xlim(hours[0], hours[-1])
    ax.grid(visible=True)
    ax.set_xlabel("Uhrzeit")
    ax.set_ylabel('Leistung in W')
    ax.legend(loc='upper right', fontsize='small', frameon=True)
    ax
    return ax, fig, first, last


@app.cell
def __(mo):
    wel = mo.md(
        """

        Der *Gesamtertrag* $E$ wird durch Integration der *Leistung* $P$ über den Tag ermittelt:

        $$
        E = \int_{t=t_0}^{t_1} P(t) \, \mathrm dt
        $$

        Der Wert von $E$ wird über eine einfache Simpson-Regel numerisch berechnet.

        Die *Volllaststunden* $V$ ergeben sich aus dem Verhältnis von Gesamtertrag $E$ und der *installierten Nennleistung* $P_N$:

        $$
        V = \\frac{E}{P_N}.
        $$

        """
    )
    return wel,


@app.cell
def __(mo, wel):
    mo.accordion(
        {"Berechnung des Gesamtertrages und der Volllaststunden": wel}
    )
    return


@app.cell
def __(I, P, mo, np):
    mo.md(
        f'''
        Gesamtertrag:
        **{mo.as_html('{0:.3f}'.format(I / 3600000))} kWh**

        Volllaststunden: **{mo.as_html('{0:.2f}'.format(I / 3600 / np.sum(P)))} h**
        '''
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        <span style="font-size:0.7em;">
        ©️ 2024 • Ralph-Uwe Börner • 
        @ruboerner@mastodon.social
        </span>
        """
    )
    return


if __name__ == "__main__":
    app.run()
