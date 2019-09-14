# -*- coding: utf-8 -*-
# --------------------------------------------------------
# decode kt_player Alfa-addon
# --------------------------------------------------------

def decode(video_url, license_code, _size=16):
    d = video_url.split("/")[1:]
    h = d[6][:2 * _size]

    v = e(license_code, _size)
    if v and h:
        t = h

        u = len(h)-1
        for u in range(u, -1, -1):
            ind = u

            k = u
            for k in range(k, len(v)):
               ind += int(v[k])

            while ind >= len(h):
               ind -= len(h)

            a = ""
            for i in range(len(h)):
                if i == u:
                   a += h[ind]
                elif i == ind:
                   a += h[u]
                else:
                   a += h[i]
            h = a

        d[6] = d[6].replace(t, h);
        d.pop(0);
        video_url = "/".join(d);

    return video_url

def e(license_code, _size):
    p = license_code
    d = p
    s = ""

    for i in range(1,len(d)):
        if d[i]:
            s += str(d[i])
        else:
            s += str(1)

    p = int(len(s)/2)
    n = int(s[:p + 1])
    m = int(s[p:])

    i = m - n;
    if i < 0:
        i = -i
    s = i
 
    i = m - n
    if i < 0:
        i = -i;
    s += i;
    s *= 2;
    s = str(s);

    rate = _size / 2 + 2

    res = ""
    for i in range(p+1):
        for x in range(1,5):
            num = int(d[i+x]) + int(s[i])
            if num >= rate:
                num -= rate
            res += str(num)

    return res
