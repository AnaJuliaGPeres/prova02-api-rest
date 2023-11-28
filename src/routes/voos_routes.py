from datetime import datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import select
from fastapi import HTTPException


from src.config.database import get_session
from src.models.voos_model import Voo

voos_router = APIRouter(prefix="/voos")


@voos_router.post("")
def cria_voo(voo: Voo):
    with get_session() as session:
        LIMITE_HORAS = 5
        hora_atual = datetime.now()
        hora_limite = hora_atual + timedelta(hours=LIMITE_HORAS)
        no_horario_limite = voo.data_saida <= hora_limite
        print("horario_limite", no_horario_limite, hora_limite)
        if no_horario_limite:
            return JSONResponse(
                content={
                    "message": f"Impossível incluir vôos com menos de {LIMITE_HORAS} horas antes da saída"
                },
                status_code=403,
            )

        session.add(voo)
        session.commit()
        session.refresh(voo)
        return voo

@voos_router.get("/vendas")
def lista_voos_venda():
    LIMITE_HORAS = 2
    with get_session() as session:
        hora_limite = datetime.now() + timedelta(hours=LIMITE_HORAS)
        statement = select(Voo).where(Voo.data_saida >= hora_limite)
        voo = session.exec(statement).all()
        return voo


@voos_router.get("")
def lista_voos():
    with get_session() as session:
        statement = select(Voo)
        voo = session.exec(statement).all()
        return voo
    
    # TODO - Implementar rota que retorne as poltronas por id do voo
    
@voos_router.get("/{voo_id}/poltronas")
def obter_poltronas_por_voo(voo_id: int):
    with get_session() as session:
        # Verifica se o voo existe
        voo = session.exec(select(Voo).where(Voo.id == voo_id)).first()

        if not voo:
            raise HTTPException(
                status_code=404,
                detail=f"Voo com ID {voo_id} não encontrado."
            )

        # Obtém as reservas associadas ao voo
        reservas = session.exec(
            select(Reserva).where(Reserva.voo_id == voo_id)
        ).all()

        poltronas_reservadas = [reserva.poltrona for reserva in reservas if reserva.poltrona is not None]

        # Gera a lista de poltronas disponíveis (considerando um total fixo de poltronas no voo)
        total_poltronas = voo.total_poltronas
        poltronas_disponiveis = [i for i in range(1, total_poltronas + 1) if i not in poltronas_reservadas]

        return {
            "id_voo": voo.id,
            "poltronas_reservadas": poltronas_reservadas,
            "poltronas_disponiveis": poltronas_disponiveis
        }


