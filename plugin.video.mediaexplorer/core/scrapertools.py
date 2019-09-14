# -*- coding: utf-8 -*-
from core.libs import *


def find_single_match(text, pattern, index=0, flags=re.DOTALL):
    try:
        matches = re.findall(pattern, text, flags)
        return matches[index]
    except Exception:
        return ''


def find_multiple_matches(text, pattern, flags=re.DOTALL):
    return re.findall(pattern, text, flags)


def get_season_and_episode(title):
    """
    Retorna el numero de temporada y de episodio obtenido del titulo de un episodio
    Ejemplos de diferentes valores para title y su valor devuelto:
        "serie 101x1.strm", "s101e1.avi", "t101e1.avi"  -> (101, 01)
        "Name TvShow 1x6.avi" -> (1, 06)
        "Temp 3 episodio 2.avi" -> (3, 02)
        "Alcantara season 13 episodie 12.avi" -> (13, 12)
        "Temp1 capitulo 14" -> (1, 14)
        "Temporada 1: El origen Episodio 9" -> None (entre el numero de temporada y los episodios no puede haber otro texto)
        "Episodio 25: titulo episodio" -> None (no existe el numero de temporada)
        "Serie X Temporada 1" -> None (no existe el numero del episodio)
    @type title: str
    @param title: titulo del episodio de una serie
    @rtype: (int, int)
    @return: Tupla formada por el numero de temporada y el del episodio o None si no se han encontrado
    """
    logger.trace()
    ret = None

    patrons = ["(\d+)x(\d+)",
               "(?:s|t)(\d+)e(\d+)",
               "(?:season|temp\w*)\s*(\d+)\s*(?:capitulo|epi\w*)\s*(\d+)"]

    for patron in patrons:
        try:
            matches = re.compile(patron, re.I).search(title)
            if matches:
                season = int(matches.group(1))
                episode = int(matches.group(2))
                logger.info("'%s' -> season: %s, episode: %s" % (title, season, episode))
                ret = (season, episode)
                break
        except:
            pass

    return ret
