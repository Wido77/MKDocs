# <b>CASA47</b>

Fecha: 07-09-2026
Estado: En curso

## <b>Lo que se investiga</b>
En esta primera investigación vamos a intentar descubrir todos los datos posibles del dominio: 
[CASA47](https://portal.casa47.es/) <b>https://portal.casa47.es</b>  y todo lo relacionado con su contratación y demás información que sea de utilidad
![indexcasa47](../assets/images/casa47/casa47_index.png)

## <b>Hallazgos</b>
- Lo primero que se debe hacer al investigar cualquier dominio es realizar un whois para ver qué tenemos delante. En este caso, al ser un dominio .es tenemos que ir a [dominios.es](https://www.dominios.es/es).<br><br>
![Whois de casa47.es](../assets/images/casa47/whois.png)
- Podemos ver que el titular del dominio es el ya extinto [SEPES](https://es.wikipedia.org/wiki/CASA_47) (Entidad Pública Empresarial de Suelo) renombrado a casa47 por motivos ideológicos al referirse directamente al artículo 47 de la Constitución.
- El dominio se registró el 22 de septiembre de 2025 que nos puede ser útil cuando comprobemos el contrato de la web e infraestructura.
- Aparece el nombre de [Emilio García Gil](https://www.linkedin.com/in/emilio-garcia-gil-1bb16521/), que, haciendo una búsqueda rápida en Google nos muestra que es el encargado directo de Sistemas y Comunicaciones de SEPES 
![Emilio](../assets/images/casa47/emilio.PNG)

- El siguiente paso es reconstruir el DNS para averigurar qué registros existen y saber si el CNAME ha pasado por infraestructuras distintas desde 2025. Estos son los comandos que vamos a utilizar y que, a continuación, se explica brevemente su funcionamiento:
```bash
nslookup -type=CNAME portal.casa47.es
nslookup -type=A portal.casa47.es
nslookup -type=AAAA portal.casa47.es
nslookup -type=TXT portal.casa47.es
nslookup -type=NS casa47.es
nslookup -type=MX casa47.es


```

```bash
nslookup -type=CNAME portal.casa47.es
```
- El primer comando nos da información muy relevante sobre el registro CNAME que redirige al dominio público:
Nos encontramos ante un backend de [Microsoft Power Pages](https://www.microsoft.com/es-es/power-platform/products/power-pages/) en el que se integra de forma nativa [Dataverse](https://www.microsoft.com/es-es/power-platform/dataverse) para implementar el SIG correspondiente.
Podemos inferir que es un entorno de producción para el público.
![nslookup](../assets/images/casa47/nslookup1.PNG)

```bash
nslookup -type=A portal.casa47.es
```
- El segundo comando nos revela la IPv4 <b>(150.171.109.82) </b>en donde presuntamente está alojada la web, pero mirando la cadena de nombres se puede deducir que simplemente resuelve hacia la infraestructura de Azure Front Door. Sería un ejercicio interesante 
saber dónde está realmente alojada la aplicación.
![nslookup2](../assets/images/casa47/nslookup2.PNG)

En este caso, vamos a intentar averiguar dónde se encuentra alojada realmente. <br> El primer paso es ejecutar el siguiente comando contra casa47.es y portal.casa47.es para saber cuales son los servidores DNS autoritativos: <br>
```bash
nslookup -type=NS casa47.es
nslookup -type=NS portal.casa47.es
```
¿Quién gestiona el DNS de casa47.es?<br>
![nslookup3](../assets/images/casa47/nslookup3.PNG)<br>
Nos encontramos con dos servidores DNS que investigaremos más adelante:<br>
	- ns1.cp2gestion-dtc-ib.com<br>
	- ns2.cp2gestion-dtc-ib.com<br><br>
¿Quién gestiona el DNS de portal.casa47.es<br>
![nslookup4](../assets/images/casa47/nslookup4.PNG)<br>

Con el anterior comando hemos llegado al servidor DNS "final" y podemos descubrir la IP con _nslookup -type=A_:<br>
![nslookup5](../assets/images/casa47/nslookup5.PNG)<br>

Ahora ya tenemos 2 ips diferentes para el "mismo" servidor, eso hace que se pueda llegar a la posible conclusión de que nos encontramos ante un servidor que NO es único,sino parte de una infraestructura distribuida.

Vamos a ejecutar un curl -I para enviar una solicitud HTTP HEAD para que el servidor nos responda solamente con los encabezados y obviar el cuerpo de la página.
![nslookup6](../assets/images/casa47/nslookup6.PNG)<br>


## Comandos



## Capturas

Sustituye el bloque de color pegando aquí tu pantallazo real (Ctrl+V).

## Archivos
- [Notas de ejemplo](../archivos/notes.txt)

## Siguientes pasos
- [ ] Leer X
- [ ] Probar Y