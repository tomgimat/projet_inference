import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os
from bs4 import BeautifulSoup as bs
import requests
import json


# Cette fonction récupère les données du site jeuxdemots.org en fonction du mot, du type d'entité (entrant ou sortant) et de la relation.
# Retourne une liste contenant les codes HTML des entités trouvées
def obtenirDepuisURL(mot, entrant, relation):
    with requests.Session() as s:
        url = 'http://www.jeuxdemots.org/rezo-dump.php?'
        if entrant:
            payload = {'gotermsubmit': 'Chercher', 'gotermrel': mot,'relation' : relation,'relin': 'norelout' }
        else:
            payload = {'gotermsubmit': 'Chercher', 'gotermrel': mot, 'relation':relation ,'relout': 'norelin'}

        r = s.get(url, params=payload)
        soup = bs(r.text, 'html.parser')
        prod = soup.find_all('code')
        while("MUTED_PLEASE_RESEND" in str(prod)):
            r = s.get(url, params=payload)
            soup = bs(r.text, 'html.parser')
            prod = soup.find_all('code')

    return prod


# Cette fonction crée un fichier texte contenant les codes HTML des entités trouvées, en fonction du mot, du type d'entité et de la relation
def creerFichierTxt(mot, entrant, relation):
    prod = obtenirDepuisURL(mot, entrant, relation)
    mot = mot.replace(" ", "_")
    mot = mot.replace("'", "")
    if entrant:
        nomFichierTxt = mot.replace(" ", "_") +relation+ "_e.txt"
    else:
        nomFichierTxt = mot.replace(" ", "_") +relation+ "_s.txt"

    try:
        tailleFichier = os.path.getsize(nomFichierTxt)
    except OSError:
        tailleFichier = 0

    if tailleFichier == 0:
        if entrant:
            nomFichierTxt = mot.replace(" ", "_") + relation+"_e.txt"
        else:
            nomFichierTxt = mot.replace(" ", "_") + relation+"_s.txt"

        fichierTxt = open(nomFichierTxt, "w", encoding="utf-8")
        fichierTxt.write(str(prod))
        fichierTxt.close()

    return nomFichierTxt


# Cette fonction crée un fichier JSON à partir d'un fichier texte contenant les codes HTML des entités trouvées par rapport au site.
def creerJSON(mot, entrant, relation):
    mot = mot.replace(" ", "_")
    mot = mot.replace("'", "")
    if entrant:
        jsonFileName = mot +relation+"_e.json"
    else:
        jsonFileName = mot + relation+"_s.json"
    try:
        tailleFichier = os.path.getsize(jsonFileName)
    except OSError:
        tailleFichier = 0

    if True:
        if entrant:
            fichierTxt = open(mot +relation+ "_e.txt", "r", encoding="utf-8")
        else:
            fichierTxt = open(mot +relation+ "_s.txt", "r", encoding="utf-8")
        lignes = fichierTxt.readlines()
        fichierJSON = open(jsonFileName, "w", encoding="utf-8")

        champs_nt = ['ntname']
        champs_e = ["name", "type", "w", "formated name"]
        champs_rt = ['trname', 'trgpname', 'rthelp']
        champs_r = ["node1", "node2", "type", "w"]

        dict0 = {}
        dict_e = {}
        dict_rt = {}
        dict_r = {}
        dict_nt = {}

        for i in range(len(lignes)):
            description = list(convertir(lignes[i].strip()))
            if (len(description) > 0):
                if description[0] == "nt":
                    dict2 = {}
                    id = description[1]
                    for i in range(1):
                        dict2[champs_nt[i]] = description[i + 2]

                    dict_nt[id] = dict2

                elif description[0] == "e":
                    dict2 = {}
                    id = description[1]
                    for i in range(3):
                        dict2[champs_e[i]] = description[i + 2]

                    if len(description) > 5:
                        dict2[champs_e[3]] = description[5]

                    dict_e[id] = dict2

                elif description[0] == "rt":
                    dict2 = {}
                    id = description[1]
                    for i in range(2):
                        dict2[champs_rt[i]] = description[i + 2]

                    if len(description) > 4:
                        dict2[champs_rt[2]] = description[4]

                    dict_rt[id] = dict2

                elif (description[0] == "r"):
                    dict2 = {}
                    id = description[1]
                    for i in range(4):
                        dict2[champs_r[i]] = description[i + 2]
                    dict_r[id] = dict2

        dict0["nt"] = dict_nt
        dict0["e"] = dict_e
        dict0["r"] = dict_r
        dict0["rt"] = dict_rt
        json.dump(dict0, fichierJSON, indent=4)

        fichierJSON.close()
        fichierTxt.close()
    return jsonFileName


# Cette fonction convertit une expression contenant des apostrophes et des points-virgules en une liste de mots.
def convertir(expression):
    resultat = []
    tmp = ""
    cond = False
    for i in range(len(expression)):
        if i + 1 == len(expression):
            tmp += expression[i]
            resultat.append(tmp)
        else:
            if expression[i] == "\'" and expression[i + 1] != ";":
                cond = True
            elif expression[i] == "\'" and expression[i + 1] == ";":
                cond = False
            if cond == True:
                tmp += expression[i]
            if cond == False and expression[i] != ";":
                tmp += expression[i]
            elif cond == False and expression[i] == ";":
                resultat.append(tmp)
                tmp = ""

    return resultat


# Prend un mot, un type d'entité (true si entrant) et une relation,
# puis charge les données json en utilisant les fonctions creerFichierTxt et creerJSON
def fetch_data(mot, entrant, relation):
    creerFichierTxt(mot, entrant, relation)
    creerJSON(mot, entrant, relation)
    mot = mot.replace(" ", "_")
    if entrant:
        nomFichierJSON = mot +relation+ "_e.json"
    else:
        nomFichierJSON = mot +relation+ "_s.json"
    fichierJSON = open(nomFichierJSON, "r")
    donnees = json.load(fichierJSON)
    fichierJSON.close()
    return donnees


#Cette fonction récupère les entités génériques pour un mot donné 
#en utilisant des relations du site pour la généralisation ("r_isa" et "r_holo"). 
#Elle exclut la relation utilisée dans la recherche initiale
def getGeneric(donnees, idMot, mot, relation):
    dict_generalisation = {"r_isa": "6", "r_holo": "10"} #dict des 
    if relation in dict_generalisation:
        del dict_generalisation[relation]
    resultat = {}
    for key in dict_generalisation:
        resultat[key] = obtenirEntiteTransitive(donnees, dict_generalisation[key], idMot, mot, key)
    return resultat

#Cette fonction récupère des entités (hyponymes) spécifiques pour un mot donné
#en utilisant des relations du site pour la spécialisation ("r_hypo" et "r_has_part").
#Elle exclut la relation utilisée dans la recherche initiale (relation).
def getSpecific(donnees, idMot, mot, relation):
    dict_specialisation = {"r_hypo": "8", "r_has_part": "9"}
    if relation in dict_specialisation:
        del dict_specialisation[relation]
    resultat = {}
    for key in dict_specialisation:
        resultat[key] = obtenirEntiteTransitive(donnees, dict_specialisation[key], idMot, mot, key)
    return resultat


# Identifie l'ID d'une relation dans les données json
def get_idRelation(relation, donnees):
    jsonDataRt = donnees["rt"]
    idRelation = -1
    for entity in jsonDataRt:
        name = jsonDataRt[entity]['trname']
        x = name.replace("'", "", 2)
        if x == relation:
            idRelation = entity
            break
    return idRelation


# Identifie l'ID d'une entité dans les données json
def get_idEntite(mot, entite, donnees):
    jsonData = donnees["e"]

    idEntite = -1
    idMot = -1
    for entity in jsonData:
        name = jsonData[entity]['name']
        x = name.replace("'", "", 2)
        if x == entite:
            idEntite = entity
        if x == mot:
            idMot = entity

    result = {"idEntite": idEntite, "idMot": idMot}
    return result

# Cette fonction vérifie si une entité donnée
# est liée à la relation donnée, indiquant une relation entrante ou non
def estRelationEntrante(idEntite, idRelation, donnees):
    jsonDataR = donnees["r"]
    resultat = False
    w = ""
    for entity in jsonDataR:
        node2 = jsonDataR[entity]['node1']
        x = node2.replace("'", "", 2)
        type = jsonDataR[entity]['type']
        y = type.replace("'", "", 2)
        w = jsonDataR[entity]["w"]

        if x == idEntite and y == idRelation:
            resultat = True
            break
    return [resultat, w]


# Cette fonction vérifie si une entité donnée
# est liée à la relation donnée, indiquant une relation sortante positive ou non
def estRelSortantePositive(idEntite, idRelation, donnees):
    jsonDataR = donnees["r"]
    resultat = False
    for entity in jsonDataR:
        node2 = jsonDataR[entity]['node2']
        x = node2.replace("'", "", 2)
        type = jsonDataR[entity]['type']
        y = type.replace("'", "", 2)
        if x == idEntite and y == idRelation and ("-" not in jsonDataR[entity]["w"]):
            resultat = True
            break
    return resultat


# Cette fonction vérifie si une entité donnée
# est liée à la relation donnée, indiquant une relation sortante negative ou non
def estRelSortanteNegative(idEntite, idRelation, donnees):
    jsonDataR = donnees["r"]
    resultat = False
    for entity in jsonDataR:
        node2 = jsonDataR[entity]['node2']
        x = node2.replace("'", "", 2)
        type = jsonDataR[entity]['type']
        y = type.replace("'", "", 2)

        if x == idEntite and y == idRelation and ("-" in jsonDataR[entity]["w"]):
            resultat = True
            break
    return resultat


# Cette fonction parcourt de manière récursive les données JSON pour rechercher des entités transitives
# (entités connectées via plusieurs relations) en fonction d'une relation donnée.
def obtenirEntiteTransitive(donnees, idRelation, idMot, mot, relation):
    jsonDataE = donnees["e"]
    jsonDataR = donnees["r"]
    resultat = []
    for relation in jsonDataR:
        if (jsonDataR[relation]['type'] == idRelation and ("-") not in jsonDataR[relation]['w']):
            node2 = jsonDataR[relation]['node2']
            x = node2.replace("'", "", 2)
            if (jsonDataE[x]['type'] == '1' and x != idMot):
                resultat.append([x, jsonDataE[x]['name'], jsonDataR[relation]['w']])
    resultat = sorted(resultat, key=poids, reverse=True)
    if len(resultat) == 0:
        dataRel = fetch_data(mot, True, relation)
        jsonDataE = dataRel["e"]
        jsonDataR = dataRel["r"]
        for relation in jsonDataR:
            if (jsonDataR[relation]['type'] == idRelation and ("-") not in jsonDataR[relation]['w']):
                node2 = jsonDataR[relation]['node2']
                x = node2.replace("'", "", 2)
                if (jsonDataE[x]['type'] == '1' and x != idMot):
                    resultat.append([x, jsonDataE[x]['name'], jsonDataR[relation]['w']])
        resultat = sorted(resultat, key=poids, reverse=True)

    return resultat


# Utilisé dans main pour inférer de façon transitive les mots et relations données
def infer_transitif(donnees, donneesEnt, idMot, idEntite, idRelation, mot, relation, entite, cpt=1):
    idCommuns = obtenirEntiteTransitive(donnees, idRelation, idMot, mot, relation)
    message = ""
    for idCommun in idCommuns:
        if cpt > 0:
            teste = estRelationEntrante(idCommun[0], idRelation, donneesEnt)
            isRelE = teste[0]
            if isRelE:
                if "-" not in teste[1]:
                    message += "oui car " + mot + " " + relation + " " + idCommun[1].replace("'", "") + " (Poids : "+idCommun[2].replace("'", "")+")\n"
                    message += "et " + idCommun[1].replace("'", "") + " " + relation + " " + entite + "(Poids : "+teste[1].replace("'", "")+")\n"
                    print("oui car " + mot + " " + relation + " " + idCommun[1].replace("'", "") + " (Poids : "+idCommun[2].replace("'", "")+")")
                    print("et " + idCommun[1].replace("'", "") + " " + relation + " " + entite + "(Poids : "+teste[1].replace("'", "")+")")
                    cpt = cpt - 1
                else:
                    message += "non car " + mot + " " + relation + " " + idCommun[1].replace("'", "")
                    message += "\net " + idCommun[1].replace("'", "") + " " + relation + " " + entite + " est faux" + "(Poids : "+teste[1].replace("'", "")+")\n"
                    print("non car " + mot + " " + relation + " " + idCommun[1].replace("'", ""))
                    print("et " + idCommun[1].replace("'", "") + " " + relation + " " + entite + " est faux" + "(Poids : "+teste[1].replace("'", "")+")")
                    cpt = cpt - 1
    return message


# Utilisé dans main pour inférer de façon déductive les mots et relations données
def infer_deductif(donnees, donneesEnt, idMot, idEntite, idRelation, mot, relation, entite, cpt=1):
    idCommuns = getGeneric(donnees, idMot, mot, relation)
    message = ""
    for idCommun in idCommuns:
        for entity in idCommuns[idCommun]:
            if cpt > 0:
                teste = estRelationEntrante(entity[0], idRelation, donneesEnt)
                isRelE = teste[0]

                if isRelE:
                    if "-" not in teste[1]:
                        message += "oui car " + mot + " " + idCommun + " " + entity[1].replace("'", "")+" (Poids : "+entity[2].replace("'", "")+")\n"
                        message += "et " + entity[1].replace("'", "") + " " + relation + " " + entite + "(Poids : "+teste[1].replace("'", "")+"\n"
                        print("oui car " + mot + " " + idCommun + " " + entity[1].replace("'", "")+" (Poids : "+entity[2].replace("'", "")+")")
                        print("et " + entity[1].replace("'", "") + " " + relation + " " + entite + "(Poids : "+teste[1].replace("'", "")+")")
                        cpt -= 1
                    else:
                        message += "non car " + mot + " " + idCommun + " " + entity[1].replace("'", "")+"\n"
                        message += "et " + entity[1].replace("'", "") + " " + relation + " " + entite + " est faux" + "(Poids : "+teste[1].replace("'", "")+")\n"
                        print("non car " + mot + " " + idCommun + " " + entity[1].replace("'", ""))
                        print("et " + entity[1].replace("'", "") + " " + relation + " " + entite + " est faux" + "(Poids : "+teste[1].replace("'", "")+")")
                        cpt = cpt - 1
    return message


# Utilisé dans main pour inférer de façon inductive les mots et relations données
def infer_inductif(donnees, donneesEnt, idMot, idEntite, idRelation, mot, relation, entite, cpt=1):
    message = ""
    negative = 0
    idCommuns = getSpecific(donnees, idMot, mot, relation)
    for idCommun in idCommuns:
        for entity in idCommuns[idCommun]:
            if cpt > 0:
                teste = estRelationEntrante(entity[0], idRelation, donneesEnt)
                isRelE = teste[0]
                if isRelE:
                    if "-" not in teste[1]:
                        message += "oui car " + mot + " " + idCommun + " " + entity[1].replace("'", "")+" (Poids : "+entity[2].replace("'", "")+")\n"
                        message += "et " + entity[1].replace("'", "") + " " + relation + " " + entite + "(Poids : "+teste[1].replace("'", "")+")\n"
                        print("oui car " + mot + " " + idCommun + " " + entity[1].replace("'", "")+" (Poids : "+entity[2].replace("'", "")+")")
                        print("et " + entity[1].replace("'", "") + " " + relation + " " + entite + "(Poids : "+teste[1].replace("'", "")+")")
                        cpt -= 1
                    else:
                        negative += 1
                        if(negative == len(idCommuns)):
                            message += "non car " + mot + " " + idCommun + " " + entity[1].replace("'", "")+"\n"
                            message += "et " + entity[1].replace("'", "") + " " + relation + " " + entite + " est faux\n"

                            print("non car " + mot + " " + idCommun + " " + entity[1].replace("'", ""))
                            print("et " + entity[1].replace("'", "") + " " + relation + " " + entite + " est faux")
                            cpt = cpt - 1
    return message


def poids(M):
    return int(M[2])


def main():
    mot1 = input("Premier mot : \n")
    relation = input("Relation : \n")
    mot2 = input("Deuxième mot : \n")

    donnees_mot1 = fetch_data(mot1, True, "")
    donnees_mot2 = fetch_data(mot2, False, "")

    infos = get_idEntite(mot1, mot2, donnees_mot1)
    idMot1 = infos["idMot"]
    idEntite1 = infos["idEntite"]

    idRelation1 = get_idRelation(relation, donnees_mot1)

    message_transitive = infer_transitif(donnees_mot1, donnees_mot2, idMot1, idEntite1, idRelation1, mot1, relation, mot2)
    print("Transitive?", message_transitive)

    message_deduction = infer_deductif(donnees_mot1, donnees_mot2, idMot1, idEntite1, idRelation1, mot1, relation, mot2)
    print("Déductive?", message_deduction)

    message_induction = infer_inductif(donnees_mot1, donnees_mot2, idMot1, idEntite1, idRelation1, mot1, relation, mot2)
    print("Inductive?", message_induction)


if __name__ == "__main__":
    main()

